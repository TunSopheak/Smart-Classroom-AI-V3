from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.class_group import ClassGroup
from app.models.class_session import ClassSession
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.subject import Subject
from app.models.weekly_schedule import WeeklySchedule


DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def ensure_academic_schema(db: Session):
    """Small SQLite-safe migration for Stage 8.1."""

    inspector = inspect(db.bind)

    if "class_groups" in inspector.get_table_names():
        existing = {column["name"] for column in inspector.get_columns("class_groups")}
        columns = {
            "department": "VARCHAR(30) DEFAULT 'CS'",
            "generation": "INTEGER DEFAULT 27",
            "year_level": "INTEGER DEFAULT 3",
            "section": "VARCHAR(30) DEFAULT 'M4'",
            "building": "VARCHAR(30) DEFAULT 'B'",
            "room_number": "VARCHAR(30) DEFAULT '108'",
        }

        for name, definition in columns.items():
            if name not in existing:
                db.execute(text(f"ALTER TABLE class_groups ADD COLUMN {name} {definition}"))

    if "class_sessions" in inspector.get_table_names():
        existing = {column["name"] for column in inspector.get_columns("class_sessions")}
        if "source" not in existing:
            db.execute(text("ALTER TABLE class_sessions ADD COLUMN source VARCHAR(60) DEFAULT 'manual'"))
        if "schedule_id" not in existing:
            db.execute(text("ALTER TABLE class_sessions ADD COLUMN schedule_id INTEGER"))

    db.commit()


def _clean_code(value: str) -> str:
    return "".join(ch for ch in value.strip().upper() if ch.isalnum())


def generate_class_code(
    department: str,
    generation: int,
    year_level: int,
    section: str,
) -> str:
    dept = _clean_code(department or "CS")
    sec = _clean_code(section or "M4")
    return f"{dept}-G{int(generation)}-Y{int(year_level)}-{sec}"


def generate_class_name(
    department: str,
    generation: int,
    year_level: int,
    section: str,
) -> str:
    dept = _clean_code(department or "CS")
    sec = _clean_code(section or "M4")
    return f"{dept} Generation {int(generation)} Year {int(year_level)} {sec}"


def generate_room(building: str, room_number: str) -> str:
    building_clean = _clean_code(building or "B")
    room_clean = _clean_code(room_number or "108")
    return f"{building_clean}{room_clean}"


def _subject_acronym(subject_name: str) -> str:
    words = [
        "".join(ch for ch in word.upper() if ch.isalnum())
        for word in subject_name.strip().split()
    ]
    words = [word for word in words if word]

    if not words:
        return "SUB"

    if len(words) == 1:
        return words[0][:4]

    return "".join(word[0] for word in words)[:6]


def generate_subject_code(db: Session, subject_name: str) -> str:
    ensure_academic_schema(db)

    base = _subject_acronym(subject_name)
    if len(base) < 2:
        base = "SUB"

    existing_codes = {
        row.subject_code
        for row in db.query(Subject).filter(Subject.subject_code.like(f"{base}%")).all()
    }

    if base not in existing_codes:
        return base

    number = 2
    while f"{base}{number}" in existing_codes:
        number += 1

    return f"{base}{number}"


def list_class_groups(db: Session):
    ensure_academic_schema(db)
    return db.query(ClassGroup).order_by(ClassGroup.class_code).all()


def list_subjects(db: Session):
    ensure_academic_schema(db)
    return db.query(Subject).order_by(Subject.subject_code).all()


def list_enrollments(db: Session):
    ensure_academic_schema(db)
    return db.query(Enrollment).order_by(Enrollment.id.desc()).all()


def list_weekly_schedules(db: Session):
    ensure_academic_schema(db)
    return db.query(WeeklySchedule).order_by(
        WeeklySchedule.day_of_week,
        WeeklySchedule.start_time,
    ).all()


def list_students(db: Session):
    return db.query(Student).order_by(Student.student_code).all()


def save_class_group(
    db: Session,
    department: str = "CS",
    generation: int = 27,
    year_level: int = 3,
    section: str = "M4",
    building: str = "B",
    room_number: str = "108",
    shift: str = "Morning",
) -> ClassGroup:
    ensure_academic_schema(db)

    class_code = generate_class_code(department, generation, year_level, section)
    class_name = generate_class_name(department, generation, year_level, section)
    room = generate_room(building, room_number)

    existing = db.query(ClassGroup).filter(ClassGroup.class_code == class_code).first()

    if existing:
        existing.class_name = class_name
        existing.department = _clean_code(department or "CS")
        existing.generation = int(generation)
        existing.year_level = int(year_level)
        existing.section = _clean_code(section or "M4")
        existing.building = _clean_code(building or "B")
        existing.room_number = _clean_code(room_number or "108")
        existing.shift = shift.strip() or "Morning"
        existing.room = room
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    item = ClassGroup(
        class_code=class_code,
        class_name=class_name,
        department=_clean_code(department or "CS"),
        generation=int(generation),
        year_level=int(year_level),
        section=_clean_code(section or "M4"),
        building=_clean_code(building or "B"),
        room_number=_clean_code(room_number or "108"),
        shift=shift.strip() or "Morning",
        room=room,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def save_subject(
    db: Session,
    subject_name: str,
) -> Subject:
    ensure_academic_schema(db)

    subject_name = subject_name.strip()
    subject_code = generate_subject_code(db, subject_name)

    existing = db.query(Subject).filter(Subject.subject_name == subject_name).first()

    if existing:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    item = Subject(
        subject_code=subject_code,
        subject_name=subject_name,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def enroll_student(db: Session, student_id: int, class_group_id: int) -> Enrollment:
    ensure_academic_schema(db)

    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.class_group_id == class_group_id,
        )
        .first()
    )

    if existing:
        return existing

    item = Enrollment(student_id=student_id, class_group_id=class_group_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def save_weekly_schedule(
    db: Session,
    class_group_id: int,
    subject_id: int,
    day_of_week: int,
    start_time,
    late_time,
    end_time,
    room: str = "",
) -> WeeklySchedule:
    ensure_academic_schema(db)

    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    final_room = room.strip() if room and room.strip() else (class_group.room if class_group else "B108")

    item = WeeklySchedule(
        class_group_id=class_group_id,
        subject_id=subject_id,
        day_of_week=int(day_of_week),
        start_time=start_time,
        late_time=late_time,
        end_time=end_time,
        room=final_room,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _format_time(value) -> str:
    return value.strftime("%H:%M")


def generate_session_title(schedule: WeeklySchedule) -> str:
    day_name = DAY_NAMES[schedule.day_of_week]
    start = _format_time(schedule.start_time)
    end = _format_time(schedule.end_time)

    return (
        f"{schedule.class_group.class_code} | "
        f"{schedule.subject.subject_name} | "
        f"{day_name} {start}-{end} | "
        f"{schedule.room}"
    )


def generate_session_from_schedule(
    db: Session,
    schedule_id: int,
) -> Optional[ClassSession]:
    ensure_academic_schema(db)

    schedule = (
        db.query(WeeklySchedule)
        .filter(WeeklySchedule.id == schedule_id, WeeklySchedule.is_active == True)
        .first()
    )

    if not schedule:
        return None

    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    tomorrow_start = today_start + timedelta(days=1)

    start_dt = datetime.combine(today, schedule.start_time)
    late_dt = datetime.combine(today, schedule.late_time)
    close_dt = datetime.combine(today, schedule.end_time)

    if close_dt <= start_dt:
        close_dt += timedelta(days=1)

    existing_session = (
        db.query(ClassSession)
        .filter(
            ClassSession.schedule_id == schedule.id,
            ClassSession.start_time >= today_start,
            ClassSession.start_time < tomorrow_start,
        )
        .order_by(ClassSession.id.desc())
        .first()
    )

    if existing_session:
        db.query(ClassSession).filter(
            ClassSession.is_active == True,
            ClassSession.id != existing_session.id,
        ).update({"is_active": False})

        existing_session.title = generate_session_title(schedule)
        existing_session.class_name = schedule.class_group.class_code
        existing_session.subject = schedule.subject.subject_name
        existing_session.room = schedule.room or schedule.class_group.room
        existing_session.start_time = start_dt
        existing_session.late_time = late_dt
        existing_session.close_time = close_dt
        existing_session.is_active = True
        existing_session.source = "weekly_schedule"
        existing_session.schedule_id = schedule.id

        db.commit()
        db.refresh(existing_session)
        return existing_session

    db.query(ClassSession).filter(ClassSession.is_active == True).update(
        {"is_active": False}
    )

    session = ClassSession(
        title=generate_session_title(schedule),
        class_name=schedule.class_group.class_code,
        subject=schedule.subject.subject_name,
        room=schedule.room or schedule.class_group.room,
        start_time=start_dt,
        late_time=late_dt,
        close_time=close_dt,
        is_active=True,
        source="weekly_schedule",
        schedule_id=schedule.id,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def generate_today_session(db: Session) -> Optional[ClassSession]:
    ensure_academic_schema(db)

    today_day = datetime.now().weekday()

    schedule = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.day_of_week == today_day,
            WeeklySchedule.is_active == True,
        )
        .order_by(WeeklySchedule.start_time)
        .first()
    )

    if not schedule:
        return None

    return generate_session_from_schedule(db, schedule.id)


def seed_demo_academics(db: Session) -> dict:
    ensure_academic_schema(db)

    now = datetime.now()

    class_group = save_class_group(
        db,
        department="CS",
        generation=27,
        year_level=3,
        section="M4",
        building="B",
        room_number="108",
        shift="Morning",
    )

    subject = save_subject(db, subject_name="Computer Network")

    students = list_students(db)
    for student in students:
        enroll_student(db, student.id, class_group.id)

    start_time = (now - timedelta(minutes=5)).time().replace(microsecond=0)
    late_time = (now + timedelta(minutes=10)).time().replace(microsecond=0)
    end_time = (now + timedelta(hours=2)).time().replace(microsecond=0)

    schedule = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.class_group_id == class_group.id,
            WeeklySchedule.subject_id == subject.id,
            WeeklySchedule.day_of_week == now.weekday(),
        )
        .first()
    )

    if schedule:
        schedule.start_time = start_time
        schedule.late_time = late_time
        schedule.end_time = end_time
        schedule.room = class_group.room
        schedule.is_active = True
        db.commit()
        db.refresh(schedule)
    else:
        schedule = save_weekly_schedule(
            db,
            class_group_id=class_group.id,
            subject_id=subject.id,
            day_of_week=now.weekday(),
            start_time=start_time,
            late_time=late_time,
            end_time=end_time,
            room=class_group.room,
        )

    return {
        "class_group": class_group,
        "subject": subject,
        "schedule": schedule,
        "students_count": len(students),
    }


def academic_summary(db: Session) -> dict:
    ensure_academic_schema(db)

    return {
        "classes_count": db.query(ClassGroup).count(),
        "subjects_count": db.query(Subject).count(),
        "enrollments_count": db.query(Enrollment).count(),
        "schedules_count": db.query(WeeklySchedule).count(),
    }


# -------------------------------
# Stage 8.2B Safe CRUD Helpers
# -------------------------------

def get_class_group_by_id(db: Session, class_group_id: int):
    ensure_academic_schema(db)
    return db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()


def get_subject_by_id(db: Session, subject_id: int):
    ensure_academic_schema(db)
    return db.query(Subject).filter(Subject.id == subject_id).first()


def get_schedule_by_id(db: Session, schedule_id: int):
    ensure_academic_schema(db)
    return db.query(WeeklySchedule).filter(WeeklySchedule.id == schedule_id).first()


def update_class_group(
    db: Session,
    class_group_id: int,
    department: str = "CS",
    generation: int = 27,
    year_level: int = 3,
    section: str = "M4",
    building: str = "B",
    room_number: str = "108",
    shift: str = "Morning",
):
    ensure_academic_schema(db)

    item = get_class_group_by_id(db, class_group_id)
    if not item:
        return None

    new_code = generate_class_code(department, generation, year_level, section)
    existing = (
        db.query(ClassGroup)
        .filter(ClassGroup.class_code == new_code, ClassGroup.id != class_group_id)
        .first()
    )

    if existing:
        return item

    item.class_code = new_code
    item.class_name = generate_class_name(department, generation, year_level, section)
    item.department = _clean_code(department or "CS")
    item.generation = int(generation)
    item.year_level = int(year_level)
    item.section = _clean_code(section or "M4")
    item.building = _clean_code(building or "B")
    item.room_number = _clean_code(room_number or "108")
    item.shift = shift.strip() or "Morning"
    item.room = generate_room(building, room_number)

    db.commit()
    db.refresh(item)
    return item


def set_class_group_active(db: Session, class_group_id: int, is_active: bool):
    item = get_class_group_by_id(db, class_group_id)
    if not item:
        return None

    item.is_active = is_active
    db.commit()
    db.refresh(item)
    return item


def _generate_subject_code_excluding(db: Session, subject_name: str, subject_id: int) -> str:
    base = _subject_acronym(subject_name)
    if len(base) < 2:
        base = "SUB"

    existing_codes = {
        row.subject_code
        for row in db.query(Subject)
        .filter(Subject.subject_code.like(f"{base}%"), Subject.id != subject_id)
        .all()
    }

    if base not in existing_codes:
        return base

    number = 2
    while f"{base}{number}" in existing_codes:
        number += 1

    return f"{base}{number}"


def update_subject(db: Session, subject_id: int, subject_name: str):
    ensure_academic_schema(db)

    item = get_subject_by_id(db, subject_id)
    if not item:
        return None

    subject_name = subject_name.strip()
    item.subject_name = subject_name
    item.subject_code = _generate_subject_code_excluding(db, subject_name, subject_id)

    db.commit()
    db.refresh(item)
    return item


def set_subject_active(db: Session, subject_id: int, is_active: bool):
    item = get_subject_by_id(db, subject_id)
    if not item:
        return None

    item.is_active = is_active
    db.commit()
    db.refresh(item)
    return item


def remove_enrollment(db: Session, enrollment_id: int):
    ensure_academic_schema(db)

    item = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not item:
        return None

    db.delete(item)
    db.commit()
    return item


def update_weekly_schedule(
    db: Session,
    schedule_id: int,
    class_group_id: int,
    subject_id: int,
    day_of_week: int,
    start_time,
    late_time,
    end_time,
    room: str = "",
):
    ensure_academic_schema(db)

    item = get_schedule_by_id(db, schedule_id)
    if not item:
        return None

    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_group_id).first()
    final_room = room.strip() if room and room.strip() else (class_group.room if class_group else "B108")

    item.class_group_id = int(class_group_id)
    item.subject_id = int(subject_id)
    item.day_of_week = int(day_of_week)
    item.start_time = start_time
    item.late_time = late_time
    item.end_time = end_time
    item.room = final_room

    db.commit()
    db.refresh(item)
    return item


def set_schedule_active(db: Session, schedule_id: int, is_active: bool):
    item = get_schedule_by_id(db, schedule_id)
    if not item:
        return None

    item.is_active = is_active
    db.commit()
    db.refresh(item)
    return item

