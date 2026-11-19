
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.project_crud.list(db, skip, limit)


@router.post("/", response_model=schemas.ProjectOut, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    if not crud.user_crud.get(db, payload.owner_id):
        raise HTTPException(404, "Owner not found")
    return crud.project_crud.create(db, payload)


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    obj = crud.project_crud.get(db, project_id)
    if not obj:
        raise HTTPException(404, "Project not found")
    return obj


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    obj = crud.project_crud.get(db, project_id)
    if not obj:
        raise HTTPException(404, "Project not found")
    return crud.project_crud.update(db, obj, payload)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    obj = crud.project_crud.get(db, project_id)
    if not obj:
        raise HTTPException(404, "Project not found")
    crud.project_crud.delete(db, obj)