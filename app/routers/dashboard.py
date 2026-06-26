from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import attendance_service, student_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": attendance_service.attendance_summary(db),
        "students": student_service.get_students(db),
        "recent": attendance_service.recent_attendance(db),
    }
    return templates.TemplateResponse(request, "dashboard.html", context)
