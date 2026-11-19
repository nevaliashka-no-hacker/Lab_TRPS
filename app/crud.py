from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models

ModelT = TypeVar("ModelT", bound=models.Base)


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    def get(self, db: Session, obj_id: int) -> ModelT | None:
        return db.query(self.model).filter(self.model.id == obj_id).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelT]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: BaseModel) -> ModelT:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelT, obj_in: BaseModel) -> ModelT:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: ModelT) -> None:
        db.delete(db_obj)
        db.commit()


user_crud = CRUDBase(models.User)
project_crud = CRUDBase(models.Project)
sprint_crud = CRUDBase(models.Sprint)
task_crud = CRUDBase(models.Task)
history_crud = CRUDBase(models.History)
twin_crud = CRUDBase(models.DigitalTwin)
metric_crud = CRUDBase(models.Metric)
prediction_crud = CRUDBase(models.Prediction)
anomaly_crud = CRUDBase(models.Anomaly)
recommendation_crud = CRUDBase(models.Recommendation)
git_event_crud = CRUDBase(models.GitEvent)
cicd_crud = CRUDBase(models.CICDStatus)
tech_metric_crud = CRUDBase(models.TechMetric)
health_crud = CRUDBase(models.HealthCheck)


# ---------- Вспомогательные операции ----------
def recalculate_sprint_points(db: Session, sprint_id: int) -> models.Sprint:
    """Инвариант Sprint: total_points = Σ story_points всех задач спринта."""
    sprint = sprint_crud.get(db, sprint_id)
    if sprint is None:
        raise ValueError("Sprint not found")
    total = (
        db.query(models.Task)
        .filter(models.Task.sprint_id == sprint_id)
        .with_entities(models.Task.story_points)
        .all()
    )
    sprint.total_points = sum(p[0] for p in total)
    db.commit()
    db.refresh(sprint)
    return sprint


def log_history(
    db: Session,
    entity_type: str,
    action: str,
    user_id: int | None = None,
    task_id: int | None = None,
    sprint_id: int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> models.History:
    """Аудит-запись (BC-7)."""
    entry = models.History(
        user_id=user_id,
        task_id=task_id,
        sprint_id=sprint_id,
        entity_type=entity_type,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry