
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/twins", tags=["Digital Twin (BC-4)"])


@router.get("/", response_model=list[schemas.DigitalTwinOut])
def list_twins(db: Session = Depends(get_db)):
    return crud.twin_crud.list(db, 0, 1000)


@router.post("/", response_model=schemas.DigitalTwinOut, status_code=201)
def create_twin(payload: schemas.DigitalTwinCreate, db: Session = Depends(get_db)):
    if not crud.project_crud.get(db, payload.project_id):
        raise HTTPException(404, "Project not found")
    return crud.twin_crud.create(db, payload)


@router.get("/{twin_id}", response_model=schemas.DigitalTwinOut)
def get_twin(twin_id: int, db: Session = Depends(get_db)):
    obj = crud.twin_crud.get(db, twin_id)
    if not obj:
        raise HTTPException(404, "Twin not found")
    return obj


@router.post("/{twin_id}/predictions", response_model=schemas.PredictionOut, status_code=201)
def add_prediction(twin_id: int, payload: schemas.PredictionCreate, db: Session = Depends(get_db)):
    if not crud.twin_crud.get(db, twin_id):
        raise HTTPException(404, "Twin not found")
    payload.twin_id = twin_id
    return crud.prediction_crud.create(db, payload)


@router.post("/{twin_id}/anomalies", response_model=schemas.AnomalyOut, status_code=201)
def add_anomaly(twin_id: int, payload: schemas.AnomalyCreate, db: Session = Depends(get_db)):
    if not crud.twin_crud.get(db, twin_id):
        raise HTTPException(404, "Twin not found")
    payload.twin_id = twin_id
    return crud.anomaly_crud.create(db, payload)


@router.post(
    "/{twin_id}/recommendations",
    response_model=schemas.RecommendationOut,
    status_code=201,
)
def add_recommendation(
    twin_id: int,
    payload: schemas.RecommendationCreate,
    db: Session = Depends(get_db),
):
    if not crud.twin_crud.get(db, twin_id):
        raise HTTPException(404, "Twin not found")
    payload.twin_id = twin_id
    return crud.recommendation_crud.create(db, payload)


# ---------- Metrics (по спринту) ----------
@router.post("/metrics", response_model=schemas.MetricOut, status_code=201)
def add_metric(payload: schemas.MetricCreate, db: Session = Depends(get_db)):
    if not crud.sprint_crud.get(db, payload.sprint_id):
        raise HTTPException(404, "Sprint not found")
    return crud.metric_crud.create(db, payload)


@router.get("/metrics", response_model=list[schemas.MetricOut])
def list_metrics(sprint_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Metric)
    if sprint_id:
        q = q.filter(models.Metric.sprint_id == sprint_id)
    return q.all()