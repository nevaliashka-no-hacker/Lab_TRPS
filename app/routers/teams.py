
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=list[schemas.TeamOut])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.team_crud.list(db, skip, limit)


@router.post("/", response_model=schemas.TeamOut, status_code=201)
def create_team(payload: schemas.TeamCreate, db: Session = Depends(get_db)):
    return crud.team_crud.create(db, payload)


@router.get("/{team_id}", response_model=schemas.TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    obj = crud.team_crud.get(db, team_id)
    if not obj:
        raise HTTPException(404, "Team not found")
    return obj


@router.patch("/{team_id}", response_model=schemas.TeamOut)
def update_team(team_id: int, payload: schemas.TeamUpdate, db: Session = Depends(get_db)):
    obj = crud.team_crud.get(db, team_id)
    if not obj:
        raise HTTPException(404, "Team not found")
    return crud.team_crud.update(db, obj, payload)


@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    obj = crud.team_crud.get(db, team_id)
    if not obj:
        raise HTTPException(404, "Team not found")
    crud.team_crud.delete(db, obj)