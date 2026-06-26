from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.student import Student
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def students_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "students": student_service.get_students(db),
    }
    return templates.TemplateResponse(request, "students.html", context)


@router.post("/")
def create_student(
    student_code: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = student_service.get_by_code(db, student_code)
    if not existing:
        db.add(Student(student_code=student_code, first_name=first_name, last_name=last_name))
        db.commit()
    return RedirectResponse("/students", status_code=303)
