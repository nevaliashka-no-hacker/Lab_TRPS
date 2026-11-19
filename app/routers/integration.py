from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/integration", tags=["Integration (BC-5)"])


@router.post("/git-events", response_model=schemas.GitEventOut, status_code=201)
def receive_git_event(payload: schemas.GitEventCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.git_event_crud.create(db, payload)


@router.get("/git-events", response_model=List[schemas.GitEventOut])
def list_git_events(project_id: int | None = None, db: Session = Depends(get_db)):
    from ..models import GitEvent
    q = db.query(GitEvent)
    if project_id:
        q = q.filter(GitEvent.project_id == project_id)
    return q.all()


@router.post("/cicd-statuses", response_model=schemas.CICDStatusOut, status_code=201)
def receive_cicd_status(payload: schemas.CICDStatusCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.cicd_crud.create(db, payload)


@router.get("/cicd-statuses", response_model=List[schemas.CICDStatusOut])
def list_cicd_statuses(project_id: int | None = None, db: Session = Depends(get_db)):
    from ..models import CICDStatus
    q = db.query(CICDStatus)
    if project_id:
        q = q.filter(CICDStatus.project_id == project_id)
    return q.all()