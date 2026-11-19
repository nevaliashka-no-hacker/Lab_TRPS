from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator

from .models import (
    TaskStatus, SprintStatus, ProjectStatus, UserRole,
    AnomalySeverity, CICDStatusEnum, GitEventType,
)


# ---------- User ----------
class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.DEVELOPER


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Project (инварианты из ЛР2) ----------
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
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
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ProjectStatus] = None
    owner_id: Optional[int] = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Sprint (инвариант: end > start; total_points = Σ story_points) ----------
class SprintBase(BaseModel):
    name: str
    project_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: SprintStatus = SprintStatus.PLANNED

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be greater than start_date")
        return self


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[SprintStatus] = None


class SprintOut(SprintBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_points: int


# ---------- Task (инвариант: story_points ≥ 0, assignee exists) ----------
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    story_points: int = Field(0, ge=0)
    status: TaskStatus = TaskStatus.TODO
    priority: int = Field(3, ge=1, le=5)
    project_id: int
    sprint_id: Optional[int] = None
    assignee_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    story_points: Optional[int] = Field(None, ge=0)
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    sprint_id: Optional[int] = None
    assignee_id: Optional[int] = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# ---------- History ----------
class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    task_id: Optional[int]
    sprint_id: Optional[int]
    entity_type: str
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime


# ---------- DigitalTwin ----------
class DigitalTwinCreate(BaseModel):
    project_id: int
    model_data: Optional[Dict[str, Any]] = None


class DigitalTwinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    model_data: Optional[Dict[str, Any]]
    last_sync_at: Optional[datetime]
    version: int


# ---------- Metric (инвариант: value ≥ 0, привязана к спринту) ----------
class MetricCreate(BaseModel):
    name: str
    value: float = Field(..., ge=0)
    unit: Optional[str] = None
    sprint_id: int
    project_id: Optional[int] = None


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
    commit_sha: Optional[str] = None
    author: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class GitEventOut(GitEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received_at: datetime


class CICDStatusCreate(BaseModel):
    project_id: int
    pipeline_id: Optional[str] = None
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
    metrics: List[MetricOut]
    twin_updated: bool
    twin_version: int
    predictions: List[PredictionOut]
    anomalies: List[AnomalyOut]
    recommendations: List[RecommendationOut]