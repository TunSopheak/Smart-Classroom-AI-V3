from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def students_page(request: Request, db: Session = Depends(get_db)):
    students = student_service.get_students(db)

    context = {
        "request": request,
        "students": students,
        "total_students": len(students),
        "active_students": len([student for student in students if student.status == "active"]),
        "next_student_code": student_service.generate_next_student_code(db),
    }

    return templates.TemplateResponse(request, "students.html", context)


@router.post("/")
def create_student(
    first_name: str = Form(...),
    last_name: str = Form(...),
    status: str = Form("active"),
    db: Session = Depends(get_db),
):
    student_service.create_student(
        db,
        first_name=first_name,
        last_name=last_name,
        status=status,
    )

    return RedirectResponse("/students", status_code=303)


@router.post("/{student_id}/update")
def update_student(
    student_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    status: str = Form("active"),
    db: Session = Depends(get_db),
):
    student_service.update_student(
        db,
        student_id=student_id,
        first_name=first_name,
        last_name=last_name,
        status=status,
    )

    return RedirectResponse("/students", status_code=303)


@router.post("/{student_id}/deactivate")
def deactivate_student(student_id: int, db: Session = Depends(get_db)):
    student_service.set_student_status(db, student_id, "inactive")
    return RedirectResponse("/students", status_code=303)


@router.post("/{student_id}/activate")
def activate_student(student_id: int, db: Session = Depends(get_db)):
    student_service.set_student_status(db, student_id, "active")
    return RedirectResponse("/students", status_code=303)
