
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/history", tags=["History (BC-7)"])


@router.get("/", response_model=list[schemas.HistoryOut])
def list_history(
    task_id: int | None = None,
    sprint_id: int | None = None,
    entity_type: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.History)
    if task_id:
        q = q.filter(models.History.task_id == task_id)
    if sprint_id:
        q = q.filter(models.History.sprint_id == sprint_id)
    if entity_type:
        q = q.filter(models.History.entity_type == entity_type)
    return q.order_by(models.History.changed_at.desc()).all()