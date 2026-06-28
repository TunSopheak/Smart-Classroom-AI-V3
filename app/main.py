from contextlib import asynccontextmanager
from pathlib import Path

from app.routers import reports
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.database import SessionLocal, init_db
from app.routers import (
    academics,
    ai_monitoring,
    attendance,
    behavior_reports,
    camera,
    dashboard,
    sessions,
    students,
    system_status,
    training,
    video_records,
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
Path("media/recordings").mkdir(parents=True, exist_ok=True)
Path("media/snapshots").mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(dashboard.router)
app.include_router(academics.router)
app.include_router(students.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(behavior_reports.router)
app.include_router(training.router)
app.include_router(ai_monitoring.router)
app.include_router(camera.router)
app.include_router(system_status.router)
app.include_router(video_records.router)
app.include_router(reports.router)
