from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import attendance_service, behavior_service

router = APIRouter(prefix="/ai-monitoring", tags=["ai-monitoring"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def ai_monitoring_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": attendance_service.attendance_summary(db),
        "recent": attendance_service.recent_attendance(db, limit=10),
        "behavior": behavior_service.placeholder_behavior_summary(),
    }
    return templates.TemplateResponse(request, "ai_monitoring.html", context)
