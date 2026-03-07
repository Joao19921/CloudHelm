import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.catalog_repository import providers_summary
from app.repositories.demand_repository import (
    create_demand,
    get_demand_by_id,
    list_demands_by_owner,
    save_orchestration_result,
)
from app.schemas.demand import (
    DemandAnalysisResponse,
    DemandCreateRequest,
    DemandResponse,
    OrchestrateRequest,
    TranscriptionResponse,
)
from app.services.orchestration_service import orchestrate_demand
from app.services.terraform_service import build_terraform_modules
from app.services.transcription_service import TranscriptionService

router = APIRouter(prefix="/api", tags=["demands"])


@router.get("/providers")
def list_providers():
    return {
        "providers": [
            {"id": "aws", "name": "Amazon Web Services"},
            {"id": "gcp", "name": "Google Cloud Platform"},
            {"id": "azure", "name": "Microsoft Azure"},
            {"id": "auto", "name": "Auto (Ranking Inteligente)"},
        ]
    }


@router.get("/terraform/{provider}")
def terraform_provider(provider: str):
    if provider not in {"aws", "gcp", "azure"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid provider.")
    return build_terraform_modules(provider)


@router.post("/demands", response_model=DemandResponse, status_code=status.HTTP_201_CREATED)
def create_demand_api(
    payload: DemandCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demand = create_demand(
        db=db,
        owner_id=current_user.id,
        title=payload.title,
        raw_input=payload.raw_input,
        input_type=payload.input_type,
    )
    return DemandResponse(
        id=demand.id,
        title=demand.title,
        input_type=demand.input_type,
        raw_input=demand.raw_input,
        provider_selected=demand.provider_selected,
        status=demand.status,
        created_at=demand.created_at,
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
        )
        for d in demands
    ]


@router.post("/demands/{demand_id}/orchestrate", response_model=DemandAnalysisResponse)
def orchestrate_demand_api(
    demand_id: int,
    payload: OrchestrateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    demand = get_demand_by_id(db, demand_id=demand_id, owner_id=current_user.id)
    if not demand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demand not found.")

    result = orchestrate_demand(
        raw_input=demand.raw_input,
        provider=payload.provider,
        catalog_summary=providers_summary(db),
    )
    save_orchestration_result(
        db=db,
        demand=demand,
        provider=result["provider"],
        architecture_json=json.dumps(result["architecture"]),
        costs_json=json.dumps(result["costs"]),
        terraform_json=json.dumps(result["terraform"]),
    )
    return DemandAnalysisResponse(
        demand_id=demand.id,
        provider=result["provider"],
        architecture=result["architecture"],
        costs=result["costs"],
        terraform=result["terraform"],
        ranking=result["ranking"],
    )


@router.post("/demands/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_api(
    audio: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    result = await TranscriptionService.transcribe(audio_file=audio)
    return TranscriptionResponse(
        transcript=result.text,
        source=result.source,
        model=result.model,
    )
