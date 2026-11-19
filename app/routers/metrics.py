from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/", response_model=List[schemas.MetricOut])
def list_metrics(
    project_id: Optional[int] = None,
    deployment_id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Metric)
    if project_id:
        q = q.filter(models.Metric.project_id == project_id)
    if deployment_id:
        q = q.filter(models.Metric.deployment_id == deployment_id)
    if name:
        q = q.filter(models.Metric.name == name)
    return q.all()


@router.post("/", response_model=schemas.MetricOut, status_code=201)
def create_metric(payload: schemas.MetricCreate, db: Session = Depends(get_db)):
    return crud.metric_crud.create(db, payload)


@router.get("/{metric_id}", response_model=schemas.MetricOut)
def get_metric(metric_id: int, db: Session = Depends(get_db)):
    obj = crud.metric_crud.get(db, metric_id)
    if not obj:
        raise HTTPException(404, "Metric not found")
    return obj


@router.delete("/{metric_id}", status_code=204)
def delete_metric(metric_id: int, db: Session = Depends(get_db)):
    obj = crud.metric_crud.get(db, metric_id)
    if not obj:
        raise HTTPException(404, "Metric not found")
    crud.metric_crud.delete(db, obj)