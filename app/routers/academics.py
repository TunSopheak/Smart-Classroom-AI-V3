from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import academic_service

router = APIRouter(prefix="/academics", tags=["academics"])
templates = Jinja2Templates(directory="app/templates")


def _parse_time(value: str):
    return datetime.strptime(value, "%H:%M").time()


@router.get("/", response_class=HTMLResponse)
def academics_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": academic_service.academic_summary(db),
        "classes": academic_service.list_class_groups(db),
        "subjects": academic_service.list_subjects(db),
        "students": academic_service.list_students(db),
        "enrollments": academic_service.list_enrollments(db),
        "schedules": academic_service.list_weekly_schedules(db),
        "day_names": academic_service.DAY_NAMES,
    }
    return templates.TemplateResponse(request, "academics.html", context)


@router.post("/seed-demo")
def seed_demo_academics(db: Session = Depends(get_db)):
    academic_service.seed_demo_academics(db)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/classes")
def create_class_group(
    department: str = Form("CS"),
    generation: int = Form(27),
    year_level: int = Form(3),
    section: str = Form("M4"),
    building: str = Form("B"),
    room_number: str = Form("108"),
    shift: str = Form("Morning"),
    db: Session = Depends(get_db),
):
    academic_service.save_class_group(
        db,
        department=department,
        generation=generation,
        year_level=year_level,
        section=section,
        building=building,
        room_number=room_number,
        shift=shift,
    )
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/classes/{class_group_id}/update")
def update_class_group(
    class_group_id: int,
    department: str = Form("CS"),
    generation: int = Form(27),
    year_level: int = Form(3),
    section: str = Form("M4"),
    building: str = Form("B"),
    room_number: str = Form("108"),
    shift: str = Form("Morning"),
    db: Session = Depends(get_db),
):
    academic_service.update_class_group(
        db,
        class_group_id=class_group_id,
        department=department,
        generation=generation,
        year_level=year_level,
        section=section,
        building=building,
        room_number=room_number,
        shift=shift,
    )
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/classes/{class_group_id}/deactivate")
def deactivate_class_group(class_group_id: int, db: Session = Depends(get_db)):
    academic_service.set_class_group_active(db, class_group_id, False)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/classes/{class_group_id}/activate")
def activate_class_group(class_group_id: int, db: Session = Depends(get_db)):
    academic_service.set_class_group_active(db, class_group_id, True)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/subjects")
def create_subject(
    subject_name: str = Form(...),
    db: Session = Depends(get_db),
):
    academic_service.save_subject(db, subject_name=subject_name)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/subjects/{subject_id}/update")
def update_subject(
    subject_id: int,
    subject_name: str = Form(...),
    db: Session = Depends(get_db),
):
    academic_service.update_subject(db, subject_id=subject_id, subject_name=subject_name)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/subjects/{subject_id}/deactivate")
def deactivate_subject(subject_id: int, db: Session = Depends(get_db)):
    academic_service.set_subject_active(db, subject_id, False)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/subjects/{subject_id}/activate")
def activate_subject(subject_id: int, db: Session = Depends(get_db)):
    academic_service.set_subject_active(db, subject_id, True)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/enrollments")
def create_enrollment(
    student_id: int = Form(...),
    class_group_id: int = Form(...),
    db: Session = Depends(get_db),
):
    academic_service.enroll_student(db, student_id, class_group_id)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/enrollments/{enrollment_id}/remove")
def remove_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    academic_service.remove_enrollment(db, enrollment_id)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/schedules")
def create_schedule(
    class_group_id: int = Form(...),
    subject_id: int = Form(...),
    day_of_week: int = Form(...),
    start_time: str = Form(...),
    late_time: str = Form(...),
    end_time: str = Form(...),
    room: str = Form(""),
    db: Session = Depends(get_db),
):
    academic_service.save_weekly_schedule(
        db,
        class_group_id=class_group_id,
        subject_id=subject_id,
        day_of_week=day_of_week,
        start_time=_parse_time(start_time),
        late_time=_parse_time(late_time),
        end_time=_parse_time(end_time),
        room=room,
    )
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/schedules/{schedule_id}/update")
def update_schedule(
    schedule_id: int,
    class_group_id: int = Form(...),
    subject_id: int = Form(...),
    day_of_week: int = Form(...),
    start_time: str = Form(...),
    late_time: str = Form(...),
    end_time: str = Form(...),
    room: str = Form(""),
    db: Session = Depends(get_db),
):
    academic_service.update_weekly_schedule(
        db,
        schedule_id=schedule_id,
        class_group_id=class_group_id,
        subject_id=subject_id,
        day_of_week=day_of_week,
        start_time=_parse_time(start_time),
        late_time=_parse_time(late_time),
        end_time=_parse_time(end_time),
        room=room,
    )
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/schedules/{schedule_id}/disable")
def disable_schedule(schedule_id: int, db: Session = Depends(get_db)):
    academic_service.set_schedule_active(db, schedule_id, False)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/schedules/{schedule_id}/activate")
def activate_schedule(schedule_id: int, db: Session = Depends(get_db)):
    academic_service.set_schedule_active(db, schedule_id, True)
    return RedirectResponse(url="/academics", status_code=303)


@router.post("/schedules/{schedule_id}/generate-session")
def generate_session_from_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    academic_service.generate_session_from_schedule(db, schedule_id)
    return RedirectResponse(url="/sessions", status_code=303)


@router.post("/generate-today-session")
def generate_today_session(db: Session = Depends(get_db)):
    academic_service.generate_today_session(db)
    return RedirectResponse(url="/sessions", status_code=303)
