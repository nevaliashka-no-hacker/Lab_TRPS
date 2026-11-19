from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/monitoring", tags=["Monitoring (BC-6)"])


@router.post("/tech-metrics", response_model=schemas.TechMetricOut, status_code=201)
def add_tech_metric(payload: schemas.TechMetricCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.tech_metric_crud.create(db, payload)


@router.get("/health-checks", response_model=List[schemas.HealthCheckOut])
def list_health_checks(db: Session = Depends(get_db)):
    return crud.health_crud.list(db, 0, 1000)


@router.post("/health-checks", response_model=schemas.HealthCheckOut, status_code=201)
def add_health_check(component: str, status: str, db: Session = Depends(get_db)):
    obj = models.HealthCheck(component=component, status=status)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj