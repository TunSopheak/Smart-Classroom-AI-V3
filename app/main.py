from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import SessionLocal, init_db
from app.routers import (
    ai_monitoring,
    attendance,
    camera,
    dashboard,
    sessions,
    students,
    system_status,
    training,
)
from app.services import session_service, student_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        student_service.seed_students(db)
        session_service.seed_default_session(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Smart Classroom AI V3", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard.router)
app.include_router(students.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(training.router)
app.include_router(ai_monitoring.router)
app.include_router(camera.router)
app.include_router(system_status.router)
