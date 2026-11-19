
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[schemas.UserOut])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.user_crud.list(db, skip, limit)


@router.post("/", response_model=schemas.UserOut, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(crud.models.User).filter(crud.models.User.email == payload.email).first():
        raise HTTPException(409, "Email already exists")
    return crud.user_crud.create(db, payload)


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    obj = crud.user_crud.get(db, user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.patch("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    obj = crud.user_crud.get(db, user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    return crud.user_crud.update(db, obj, payload)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    obj = crud.user_crud.get(db, user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    crud.user_crud.delete(db, obj)