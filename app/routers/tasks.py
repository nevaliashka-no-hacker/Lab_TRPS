from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# Инвариант Task: допустимые переходы статусов (из DDD-таблицы ЛР2)
ALLOWED_TRANSITIONS = {
    models.TaskStatus.TODO: {models.TaskStatus.IN_PROGRESS},
    models.TaskStatus.IN_PROGRESS: {models.TaskStatus.REVIEW},
    models.TaskStatus.REVIEW: {models.TaskStatus.DONE, models.TaskStatus.IN_PROGRESS},
    models.TaskStatus.DONE: set(),
}


@router.get("/", response_model=List[schemas.TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    sprint_id: Optional[int] = None,
    status: Optional[models.TaskStatus] = None,
    assignee_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(models.Task)
    if project_id is not None:
        q = q.filter(models.Task.project_id == project_id)
    if sprint_id is not None:
        q = q.filter(models.Task.sprint_id == sprint_id)
    if status is not None:
        q = q.filter(models.Task.status == status)
    if assignee_id is not None:
        q = q.filter(models.Task.assignee_id == assignee_id)
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.TaskOut, status_code=201)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Проверка инвариантов Task
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    if payload.sprint_id and not crud.sprint_crud.get(db, payload.sprint_id):
        raise HTTPException(404, "Sprint not found")
    if payload.assignee_id and not crud.user_crud.get(db, payload.assignee_id):
        raise HTTPException(404, "Assignee not found")

    task = crud.task_crud.create(db, payload)

    # Пересчёт total_points спринта
    if task.sprint_id:
        crud.recalculate_sprint_points(db, task.sprint_id)

    crud.log_history(
        db, entity_type="task", action="create", task_id=task.id,
    )
    return task


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    obj = crud.task_crud.get(db, task_id)
    if not obj:
        raise HTTPException(404, "Task not found")
    return obj


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    obj = crud.task_crud.get(db, task_id)
    if not obj:
        raise HTTPException(404, "Task not found")

    # Проверка перехода статуса
    if payload.status is not None and payload.status != obj.status:
        allowed = ALLOWED_TRANSITIONS.get(obj.status, set())
        if payload.status not in allowed:
            raise HTTPException(
                400,
                f"Invalid status transition {obj.status.value} -> {payload.status.value}",
            )
        crud.log_history(
            db, entity_type="task", action="status_change", task_id=task_id,
            old_value=obj.status.value, new_value=payload.status.value,
        )

    if payload.assignee_id and not crud.user_crud.get(db, payload.assignee_id):
        raise HTTPException(404, "Assignee not found")

    old_sprint_id = obj.sprint_id
    updated = crud.task_crud.update(db, obj, payload)

    # Пересчёт total_points для спринта (старого и нового)
    if old_sprint_id:
        crud.recalculate_sprint_points(db, old_sprint_id)
    if updated.sprint_id and updated.sprint_id != old_sprint_id:
        crud.recalculate_sprint_points(db, updated.sprint_id)

    return updated


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    obj = crud.task_crud.get(db, task_id)
    if not obj:
        raise HTTPException(404, "Task not found")
    sprint_id = obj.sprint_id
    crud.task_crud.delete(db, obj)
    if sprint_id:
        crud.recalculate_sprint_points(db, sprint_id)


# ============================================================
# Сценарий ЛР2: «Создание задачи и добавление в спринт»
# (POST /tasks уже создаёт; отдельный эндпоинт для добавления в спринт)
# ============================================================
@router.post("/{task_id}/add-to-sprint/{sprint_id}", response_model=schemas.TaskOut)
def add_task_to_sprint(task_id: int, sprint_id: int, db: Session = Depends(get_db)):
    task = crud.task_crud.get(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    sprint = crud.sprint_crud.get(db, sprint_id)
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    if sprint.status == models.SprintStatus.COMPLETED:
        raise HTTPException(400, "Cannot add task to completed sprint")

    task.sprint_id = sprint_id
    db.commit()
    db.refresh(task)
    crud.recalculate_sprint_points(db, sprint_id)
    crud.log_history(
        db, entity_type="task", action="add_to_sprint",
        task_id=task_id, sprint_id=sprint_id,
    )
    return task