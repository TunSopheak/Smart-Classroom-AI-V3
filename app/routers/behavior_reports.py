from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import behavior_report_service

router = APIRouter(prefix="/behavior-reports", tags=["behavior-reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def behavior_reports_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "events": behavior_report_service.list_behavior_events(db),
        "summary": behavior_report_service.behavior_summary(db),
    }
    return templates.TemplateResponse(request, "behavior_reports.html", context)
