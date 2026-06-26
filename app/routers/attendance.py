from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def attendance_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": attendance_service.attendance_summary(db),
        "records": attendance_service.recent_attendance(db, limit=50),
    }
    return templates.TemplateResponse(request, "attendance.html", context)


@router.post("/demo-face")
def demo_face_attendance(
    student_code: str = Form(...),
    confidence: float = Form(85.0),
    db: Session = Depends(get_db),
):
    attendance_service.mark_face_attendance(db, student_code=student_code, confidence=confidence)
    return RedirectResponse("/attendance", status_code=303)
