from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application_log import ApplicationLog
from app.models.demand import Demand


def count_demands_by_owner(db: Session, owner_id: int) -> int:
    return int(db.scalar(select(func.count(Demand.id)).where(Demand.owner_id == owner_id)) or 0)

def create_demand(
    db: Session,
    owner_id: int,
    title: str,
    raw_input: str,
    input_type: str,
) -> Demand:
    demand = Demand(
        owner_id=owner_id,
        title=title,
        raw_input=raw_input,
        input_type=input_type,
        status="created",
    )
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand


def list_demands_by_owner(db: Session, owner_id: int) -> list[Demand]:
    rows = db.scalars(
        select(Demand).where(Demand.owner_id == owner_id).order_by(Demand.created_at.desc())
    )
    return list(rows)


def get_demand_by_id(db: Session, demand_id: int, owner_id: int) -> Demand | None:
    return db.scalar(
        select(Demand).where(Demand.id == demand_id, Demand.owner_id == owner_id)
    )


def save_orchestration_result(
    db: Session,
    demand: Demand,
    provider: str,
    architecture_json: str,
    costs_json: str,
    terraform_json: str,
    analysis_json: str,
) -> Demand:
    demand.provider_selected = provider
    demand.status = "orchestrated"
    demand.architecture_json = architecture_json
    demand.costs_json = costs_json
    demand.terraform_json = terraform_json
    demand.analysis_json = analysis_json
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand


def delete_demand(db: Session, demand: Demand) -> None:
    db.query(ApplicationLog).filter(ApplicationLog.demand_id == demand.id).update({ApplicationLog.demand_id: None}, synchronize_session=False)
    db.delete(demand)
    db.commit()
