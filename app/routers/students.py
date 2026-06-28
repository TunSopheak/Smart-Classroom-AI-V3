from io import BytesIO

import qrcode
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import attendance_service, student_service

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


def _student_qr_scan_url(request: Request, student) -> str:
    token = attendance_service.qr_token_for_student(student)
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/attendance/qr-scan?student_code={student.student_code}&token={token}"


def _qr_png_bytes(value: str) -> bytes:
    qr_image = qrcode.make(value)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    return buffer.getvalue()


@router.get("/{student_id}/qr", response_class=HTMLResponse)
def view_student_qr(student_id: int, request: Request, db: Session = Depends(get_db)):
    student = student_service.get_by_id(db, student_id)

    if not student:
        return RedirectResponse("/students", status_code=303)

    scan_url = _student_qr_scan_url(request, student)

    import base64
    qr_data_url = "data:image/png;base64," + base64.b64encode(_qr_png_bytes(scan_url)).decode("utf-8")

    context = {
        "request": request,
        "student": student,
        "scan_url": scan_url,
        "qr_data_url": qr_data_url,
    }

    return templates.TemplateResponse(request, "student_qr_view.html", context)


@router.get("/{student_id}/qr/download")
def download_student_qr(student_id: int, request: Request, db: Session = Depends(get_db)):
    student = student_service.get_by_id(db, student_id)

    if not student:
        return RedirectResponse("/students", status_code=303)

    scan_url = _student_qr_scan_url(request, student)
    qr_bytes = _qr_png_bytes(scan_url)

    filename = f"{student.student_code}_qr_attendance.png"

    return StreamingResponse(
        BytesIO(qr_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
