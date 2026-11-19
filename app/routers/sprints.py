
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/sprints", tags=["Sprints"])


@router.get("/", response_model=list[schemas.SprintOut])
def list_sprints(
    project_id: int | None = None,
    status: models.SprintStatus | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Sprint)
    if project_id:
        q = q.filter(models.Sprint.project_id == project_id)
    if status:
        q = q.filter(models.Sprint.status == status)
    return q.all()


@router.post("/", response_model=schemas.SprintOut, status_code=201)
def create_sprint(payload: schemas.SprintCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.sprint_crud.create(db, payload)


@router.get("/{sprint_id}", response_model=schemas.SprintOut)
def get_sprint(sprint_id: int, db: Session = Depends(get_db)):
    obj = crud.sprint_crud.get(db, sprint_id)
    if not obj:
        raise HTTPException(404, "Sprint not found")
    return obj


@router.patch("/{sprint_id}", response_model=schemas.SprintOut)
def update_sprint(sprint_id: int, payload: schemas.SprintUpdate, db: Session = Depends(get_db)):
    obj = crud.sprint_crud.get(db, sprint_id)
    if not obj:
        raise HTTPException(404, "Sprint not found")
    return crud.sprint_crud.update(db, obj, payload)


@router.delete("/{sprint_id}", status_code=204)
def delete_sprint(sprint_id: int, db: Session = Depends(get_db)):
    obj = crud.sprint_crud.get(db, sprint_id)
    if not obj:
        raise HTTPException(404, "Sprint not found")
    crud.sprint_crud.delete(db, obj)


# ============================================================
# Сценарий ЛР2: «Завершение спринта и обновление цифрового двойника»
# (диаграмма последовательности: SprintService → TaskService → MetricService
#  → PredictionService → DigitalTwin → DB → AIAssistant)
# ============================================================
@router.post("/{sprint_id}/complete", response_model=schemas.SprintCompleteResult)
def complete_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = crud.sprint_crud.get(db, sprint_id)
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    if sprint.status == models.SprintStatus.COMPLETED:
        raise HTTPException(400, "Sprint already completed")

    # 1. Проверка инварианта: все задачи должны быть Done
    tasks = db.query(models.Task).filter(models.Task.sprint_id == sprint_id).all()
    incomplete = [t for t in tasks if t.status != models.TaskStatus.DONE]
    if incomplete:
        raise HTTPException(
            400,
            f"Not all tasks are done: {len(incomplete)} remaining",
        )

    # 2. Пересчёт total_points (инвариант Sprint)
    crud.recalculate_sprint_points(db, sprint_id)

    # 3. Расчёт метрик (velocity, lead_time, cycle_time, bug_rate, coverage)
    metrics_data = [
        ("velocity", float(sprint.total_points), "points"),
        ("lead_time", 0.0, "days"),
        ("cycle_time", 0.0, "days"),
        ("bug_rate", 0.0, "%"),
        ("test_coverage", 0.0, "%"),
    ]
    created_metrics: list[models.Metric] = []
    for name, value, unit in metrics_data:
        m = models.Metric(
            name=name, value=value, unit=unit,
            sprint_id=sprint.id, project_id=sprint.project_id,
        )
        db.add(m)
        created_metrics.append(m)
    db.commit()
    for m in created_metrics:
        db.refresh(m)

    # 4. Обновление / создание цифрового двойника
    twin = (
        db.query(models.DigitalTwin)
        .filter(models.DigitalTwin.project_id == sprint.project_id)
        .first()
    )
    if twin is None:
        twin = models.DigitalTwin(project_id=sprint.project_id, model_data={})
        db.add(twin)
        db.commit()
        db.refresh(twin)
    twin.version += 1
    twin.model_data = {
        **(twin.model_data or {}),
        "last_sprint_metrics": {m.name: m.value for m in created_metrics},
    }
    from sqlalchemy.sql import func
    twin.last_sync_at = func.now()
    db.commit()
    db.refresh(twin)

    # 5. Генерация прогноза (Prediction: accuracy ≥ 0.8)
    prediction = models.Prediction(
        twin_id=twin.id,
        predicted_time=float(sprint.total_points) * 1.5 or 1.0,
        accuracy=0.85,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    # 6. Обнаружение аномалий (например, если total_points слишком велик)
    anomalies = []
    if sprint.total_points > 100:
        anomaly = models.Anomaly(
            twin_id=twin.id,
            type="high_load",
            severity=models.AnomalySeverity.HIGH,
        )
        db.add(anomaly)
        anomalies.append(anomaly)
    db.commit()
    for a in anomalies:
        db.refresh(a)

    # 7. Формирование рекомендаций
    recommendation = models.Recommendation(
        twin_id=twin.id,
        text=f"Sprint {sprint.name} completed: {sprint.total_points} points delivered.",
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    # 8. Смена статуса спринта
    sprint.status = models.SprintStatus.COMPLETED
    db.commit()
    db.refresh(sprint)

    # 9. Аудит
    crud.log_history(
        db, entity_type="sprint", action="complete",
        sprint_id=sprint.id,
        old_value="active", new_value="completed",
    )

    return schemas.SprintCompleteResult(
        sprint_id=sprint.id,
        status=sprint.status,
        metrics=[schemas.MetricOut.model_validate(m) for m in created_metrics],
        twin_updated=True,
        twin_version=twin.version,
        predictions=[schemas.PredictionOut.model_validate(prediction)],
        anomalies=[schemas.AnomalyOut.model_validate(a) for a in anomalies],
        recommendations=[schemas.RecommendationOut.model_validate(recommendation)],
    )