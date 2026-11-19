import enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text,
    Enum, Boolean, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


# ---------- Enums ----------
class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class SprintStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class UserRole(str, enum.Enum):
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    DEVOPS = "devops"
    ML_ENGINEER = "ml_engineer"


class AnomalySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CICDStatusEnum(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"


class GitEventType(str, enum.Enum):
    COMMIT = "commit"
    PUSH = "push"
    MERGE_REQUEST = "merge_request"


# ============================================================
# BC-1..BC-3: Project / Sprint / Task / User  (по ER-диаграмме ЛР1)
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DEVELOPER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owned_projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", back_populates="assignee")
    history_entries = relationship("History", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="owned_projects")
    sprints = relationship(
        "Sprint", back_populates="project", cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    twins = relationship("DigitalTwin", back_populates="project")
    git_events = relationship("GitEvent", back_populates="project")
    cicd_events = relationship("CICDStatus", back_populates="project")
    tech_metrics = relationship("TechMetric", back_populates="project")


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(SprintStatus), default=SprintStatus.PLANNED, nullable=False)
    total_points = Column(Integer, default=0, nullable=False)

    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")
    metrics = relationship("Metric", back_populates="sprint")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    story_points = Column(Integer, default=0, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")


# ============================================================
# BC-7: History (аудит)
# ============================================================
class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    entity_type = Column(String(50), nullable=False)  # project/task/sprint/...
    action = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="history_entries")


# ============================================================
# BC-4: DigitalTwin / Metric / Prediction / Anomaly / Recommendation
# ============================================================
class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    model_data = Column(JSON, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)

    project = relationship("Project", back_populates="twins")
    predictions = relationship("Prediction", back_populates="twin")
    anomalies = relationship("Anomaly", back_populates="twin")
    recommendations = relationship("Recommendation", back_populates="twin")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(40), nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    sprint = relationship("Sprint", back_populates="metrics")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(Integer, ForeignKey("digital_twins.id"), nullable=False)
    predicted_time = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    twin = relationship("DigitalTwin", back_populates="predictions")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(Integer, ForeignKey("digital_twins.id"), nullable=False)
    type = Column(String(80), nullable=False)
    severity = Column(Enum(AnomalySeverity), default=AnomalySeverity.MEDIUM)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    twin = relationship("DigitalTwin", back_populates="anomalies")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    twin_id = Column(Integer, ForeignKey("digital_twins.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    twin = relationship("DigitalTwin", back_populates="recommendations")


# ============================================================
# BC-5: Интеграция
# ============================================================
class GitEvent(Base):
    __tablename__ = "git_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    event_type = Column(Enum(GitEventType), nullable=False)
    commit_sha = Column(String(64), nullable=True)
    author = Column(String(120), nullable=True)
    payload = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="git_events")


class CICDStatus(Base):
    __tablename__ = "cicd_statuses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    pipeline_id = Column(String(80), nullable=True)
    status = Column(Enum(CICDStatusEnum), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="cicd_events")


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    request_type = Column(String(80), nullable=False)
    payload = Column(JSON, nullable=True)
    response = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# BC-6: Мониторинг
# ============================================================
class TechMetric(Base):
    __tablename__ = "tech_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="tech_metrics")


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())