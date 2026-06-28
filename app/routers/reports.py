from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def reports_center(request: Request, db: Session = Depends(get_db)):
    attendance = report_service.attendance_report(db)
    ai_events = report_service.ai_event_report(db)

    context = {
        "request": request,
        "attendance": attendance,
        "ai_events": ai_events,
    }

    return templates.TemplateResponse(request, "reports.html", context)
