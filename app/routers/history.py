from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/history", tags=["History (BC-7)"])


@router.get("/", response_model=List[schemas.HistoryOut])
def list_history(
    task_id: Optional[int] = None,
    sprint_id: Optional[int] = None,
    entity_type: Optional[str] = None,
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