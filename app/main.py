from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (
    users, projects, sprints, tasks,
    twins, integration, monitoring, history,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Digital Twin of Development Process API",
    description=(
        "REST API для управления сущностями цифрового двойника процесса разработки. "
        "Модель соответствует ЛР1 (ER: User, Project, Sprint, Task, History) "
        "и ЛР2 (DDD: BC-1…BC-7, инварианты агрегатов)."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(sprints.router)
app.include_router(tasks.router)
app.include_router(twins.router)
app.include_router(integration.router)
app.include_router(monitoring.router)
app.include_router(history.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Digital Twin of Development Process API",
        "version": "2.0.0",
        "docs": "/docs",
        "bounded_contexts": [
            "BC-1 Project Management",
            "BC-2 Task Management",
            "BC-3 Sprint Management",
            "BC-4 Digital Twin",
            "BC-5 Integration",
            "BC-6 Monitoring",
            "BC-7 History/Audit",
        ],
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}