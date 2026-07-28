import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.app_settings_repository import get_llm_runtime_config
from app.repositories.catalog_repository import list_catalog_items, providers_summary
from app.repositories.demand_repository import (
    count_demands_by_owner,
    create_demand,
    get_demand_by_id,
    list_demands_by_owner,
    save_orchestration_result,
    delete_demand,
)
from app.schemas.demand import (
    DemandAnalysisResponse,
    DemandCreateRequest,
    DemandResponse,
    OrchestrateRequest,

)
from app.services.application_log_service import ApplicationLogService
from app.services.orchestration_service import orchestrate_demand
from app.services.terraform_service import build_terraform_modules


router = APIRouter(tags=["demands"])


@router.get("/providers")
def list_providers():
    return {
        "providers": [
            {"id": "aws", "name": "Amazon Web Services"},
            {"id": "gcp", "name": "Google Cloud Platform"},
            {"id": "azure", "name": "Microsoft Azure"},
            {"id": "oci", "name": "Oracle Cloud Infrastructure"},
            {"id": "auto", "name": "Auto (Ranking Inteligente)"},
        ]
    }


@router.get("/terraform/{provider}")
def terraform_provider(provider: str):
    if provider not in {"aws", "gcp", "azure", "oci"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider.")
    return build_terraform_modules(provider)


@router.post("/demands", response_model=DemandResponse, status_code=status.HTTP_201_CREATED)
def create_demand_api(
    payload: DemandCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if count_demands_by_owner(db, current_user.id) >= 3:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Limite de 3 bases atingido. Apague uma base antes de criar outra.")

    demand = create_demand(
        db=db,
        owner_id=current_user.id,
        title=payload.title,
        raw_input=payload.raw_input,
        input_type=payload.input_type,
    )
    ApplicationLogService.record(db, event_name="base_created", event_category="execution", demand_id=demand.id, user_id=current_user.id, route="POST /api/demands", metadata={"input_type": demand.input_type}, ip_address=request.client.host if request and request.client else None, user_agent=request.headers.get("user-agent") if request else None)
    return DemandResponse(
        id=demand.id,
        title=demand.title,
        input_type=demand.input_type,
            raw_input=demand.raw_input,
        provider_selected=demand.provider_selected,
        status=demand.status,
        created_at=demand.created_at,
        has_analysis=bool(demand.analysis_json),
    )


@router.get("/demands", response_model=list[DemandResponse])
def list_demands_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demands = list_demands_by_owner(db, current_user.id)
    return [
        DemandResponse(
            id=d.id,
            title=d.title,
            input_type=d.input_type,
            raw_input=d.raw_input,
            provider_selected=d.provider_selected,
            status=d.status,
            created_at=d.created_at,
            has_analysis=bool(d.analysis_json),
        )
        for d in demands
    ]




@router.get("/demands/{demand_id}/analysis", response_model=DemandAnalysisResponse)
def get_demand_analysis_api(
    demand_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demand = get_demand_by_id(db, demand_id=demand_id, owner_id=current_user.id)
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Base arquitetural não encontrada.")
    ApplicationLogService.record(db, event_name="base_opened", event_category="interaction", demand_id=demand.id, user_id=current_user.id, route="GET /api/demands/{demand_id}/analysis", metadata={"has_analysis": bool(demand.analysis_json or demand.architecture_json)}, ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    if demand.analysis_json:
        payload = json.loads(demand.analysis_json)
    elif demand.architecture_json:
        payload = {
            "provider": demand.provider_selected or "aws",
            "architecture": json.loads(demand.architecture_json),
            "costs": json.loads(demand.costs_json or "{}"),
            "terraform": json.loads(demand.terraform_json or "{}"),
            "ranking": {},
            "ai": {},
        }
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esta base ainda não possui uma análise para abrir.")
    return DemandAnalysisResponse(demand_id=demand.id, **payload)


@router.delete("/demands/{demand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demand_api(
    demand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demand = get_demand_by_id(db, demand_id=demand_id, owner_id=current_user.id)
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Base arquitetural não encontrada.")
    ApplicationLogService.record(db, event_name="base_deleted", event_category="interaction", demand_id=demand.id, user_id=current_user.id, route="DELETE /api/demands/{demand_id}")
    delete_demand(db, demand)

@router.post("/demands/{demand_id}/orchestrate", response_model=DemandAnalysisResponse)
def orchestrate_demand_api(
    demand_id: int,
    payload: OrchestrateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demand = get_demand_by_id(db, demand_id=demand_id, owner_id=current_user.id)
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demand not found.")

    llm_config = get_llm_runtime_config(db)
    llm_provider = llm_config.get("provider", "none")
    llm_api_key = None
    if llm_provider == "openai":
        llm_api_key = llm_config.get("openai_api_key", "")
    elif llm_provider == "gemini":
        llm_api_key = llm_config.get("gemini_api_key", "")

    started_at = time.perf_counter()
    ApplicationLogService.record(db, event_name="architecture_build_started", event_category="execution", event_status="started", demand_id=demand.id, user_id=current_user.id, route="POST /api/demands/{demand_id}/orchestrate", metadata={"provider": payload.provider}, ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))

    try:
        result = orchestrate_demand(
            raw_input=demand.raw_input,
            provider=payload.provider,
            catalog_summary=providers_summary(db),
            catalog_items=list_catalog_items(db=db, provider="all", search="", limit=500),
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
            llm_model=llm_config.get("model") or None,
        )
    except Exception:
        ApplicationLogService.record(db, event_name="architecture_build_failed", event_category="execution", event_status="failed", demand_id=demand.id, user_id=current_user.id, route="POST /api/demands/{demand_id}/orchestrate", duration_ms=int((time.perf_counter() - started_at) * 1000), metadata={"provider": payload.provider}, ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
        raise
    save_orchestration_result(
        db=db,
        demand=demand,
        provider=result["provider"],
        architecture_json=json.dumps(result["architecture"]),
        costs_json=json.dumps(result["costs"]),
        terraform_json=json.dumps(result["terraform"]),
        analysis_json=json.dumps(result),
    )

    return DemandAnalysisResponse(demand_id=demand.id, **result)




