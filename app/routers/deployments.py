from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.get("/", response_model=List[schemas.DeploymentOut])
def list_deployments(
    project_id: Optional[int] = None,
    environment: Optional[models.Environment] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Deployment)
    if project_id:
        q = q.filter(models.Deployment.project_id == project_id)
    if environment:
        q = q.filter(models.Deployment.environment == environment)
    return q.all()


@router.post("/", response_model=schemas.DeploymentOut, status_code=201)
def create_deployment(payload: schemas.DeploymentCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.deployment_crud.create(db, payload)


@router.get("/{dep_id}", response_model=schemas.DeploymentOut)
def get_deployment(dep_id: int, db: Session = Depends(get_db)):
    obj = crud.deployment_crud.get(db, dep_id)
    if not obj:
        raise HTTPException(404, "Deployment not found")
    return obj


@router.patch("/{dep_id}", response_model=schemas.DeploymentOut)
def update_deployment(dep_id: int, payload: schemas.DeploymentUpdate, db: Session = Depends(get_db)):
    obj = crud.deployment_crud.get(db, dep_id)
    if not obj:
        raise HTTPException(404, "Deployment not found")
    return crud.deployment_crud.update(db, obj, payload)