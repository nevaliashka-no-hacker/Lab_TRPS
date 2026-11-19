from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from .models import (
    AnomalySeverity,
    CICDStatusEnum,
    GitEventType,
    ProjectStatus,
    SprintStatus,
    TaskStatus,
    UserRole,
)


# ---------- User ----------
class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.DEVELOPER


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Project (инварианты из ЛР2) ----------
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    owner_id: int

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be greater than start_date")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: ProjectStatus | None = None
    owner_id: int | None = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Sprint (инвариант: end > start; total_points = Σ story_points) ----------
class SprintBase(BaseModel):
    name: str
    project_id: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: SprintStatus = SprintStatus.PLANNED

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be greater than start_date")
        return self


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: SprintStatus | None = None


class SprintOut(SprintBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_points: int


# ---------- Task (инвариант: story_points ≥ 0, assignee exists) ----------
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    story_points: int = Field(0, ge=0)
    status: TaskStatus = TaskStatus.TODO
    priority: int = Field(3, ge=1, le=5)
    project_id: int
    sprint_id: int | None = None
    assignee_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    story_points: int | None = Field(None, ge=0)
    status: TaskStatus | None = None
    priority: int | None = Field(None, ge=1, le=5)
    sprint_id: int | None = None
    assignee_id: int | None = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# ---------- History ----------
class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None
    task_id: int | None
    sprint_id: int | None
    entity_type: str
    action: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime


# ---------- DigitalTwin ----------
class DigitalTwinCreate(BaseModel):
    project_id: int
    model_data: dict[str, Any] | None = None


class DigitalTwinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    model_data: dict[str, Any] | None
    last_sync_at: datetime | None
    version: int


# ---------- Metric (инвариант: value ≥ 0, привязана к спринту) ----------
class MetricCreate(BaseModel):
    name: str
    value: float = Field(..., ge=0)
    unit: str | None = None
    sprint_id: int
    project_id: int | None = None


class MetricOut(MetricCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    calculated_at: datetime


# ---------- Prediction (инвариант: accuracy ≥ 0.8, predicted_time > 0) ----------
class PredictionCreate(BaseModel):
    twin_id: int
    predicted_time: float = Field(..., gt=0)
    accuracy: float = Field(..., ge=0.8, le=1.0)


class PredictionOut(PredictionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    generated_at: datetime


# ---------- Anomaly / Recommendation ----------
class AnomalyCreate(BaseModel):
    twin_id: int
    type: str
    severity: AnomalySeverity = AnomalySeverity.MEDIUM


class AnomalyOut(AnomalyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    detected_at: datetime


class RecommendationCreate(BaseModel):
    twin_id: int
    text: str


class RecommendationOut(RecommendationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Git / CICD ----------
class GitEventCreate(BaseModel):
    project_id: int
    event_type: GitEventType
    commit_sha: str | None = None
    author: str | None = None
    payload: dict[str, Any] | None = None


class GitEventOut(GitEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received_at: datetime


class CICDStatusCreate(BaseModel):
    project_id: int
    pipeline_id: str | None = None
    status: CICDStatusEnum


class CICDStatusOut(CICDStatusCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received_at: datetime


# ---------- TechMetric / HealthCheck ----------
class TechMetricCreate(BaseModel):
    project_id: int
    name: str
    value: float


class TechMetricOut(TechMetricCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_at: datetime


class HealthCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component: str
    status: str
    checked_at: datetime


# ---------- Сценарий ЛР2: завершение спринта ----------
class SprintCompleteResult(BaseModel):
    sprint_id: int
    status: SprintStatus
    metrics: list[MetricOut]
    twin_updated: bool
    twin_version: int
    predictions: list[PredictionOut]
    anomalies: list[AnomalyOut]
    recommendations: list[RecommendationOut]