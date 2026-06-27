from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.behavior_event import BehaviorEvent
from app.models.class_group import ClassGroup
from app.models.class_session import ClassSession
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.subject import Subject
from app.models.weekly_schedule import WeeklySchedule
from app.services import academic_service


DEMO_STUDENTS = [
    ("STU0001", "Tun", "Sopheak"),
    ("STU0002", "Tit", "Sokhom"),
    ("STU0003", "Tep", "Makhon"),
    ("STU0004", "Thorn Sarey", "Rothana"),
    ("STU0005", "Theam", "Vantim"),
    ("STU0006", "Hoeun", "Sithai"),
    ("STU0007", "Chork", "Panha"),
    ("STU0008", "Hean", "Senghorn"),
    ("STU0009", "Say", "Menghorng"),
    ("STU0010", "Heang", "Bunleab"),
]


def _reset_demo_students(db: Session):
    db.query(Student).delete(synchronize_session=False)

    for code, first_name, last_name in DEMO_STUDENTS:
        db.add(
            Student(
                student_code=code,
                first_name=first_name,
                last_name=last_name,
                status="active",
            )
        )

    db.commit()
    return db.query(Student).order_by(Student.student_code).all()


def _create_demo_academics(db: Session):
    academic_service.ensure_academic_schema(db)

    class_group = academic_service.save_class_group(
        db,
        department="CS",
        generation=27,
        year_level=3,
        section="M4",
        building="B",
        room_number="108",
        shift="Morning",
    )

    iot_subject = academic_service.save_subject(
        db,
        subject_name="Internet of Things",
    )

    academic_service.save_subject(
        db,
        subject_name="Computer Network",
    )

    students = db.query(Student).order_by(Student.student_code).all()
    for student in students:
        academic_service.enroll_student(db, student.id, class_group.id)

    now = datetime.now()

    schedule = academic_service.save_weekly_schedule(
        db,
        class_group_id=class_group.id,
        subject_id=iot_subject.id,
        day_of_week=now.weekday(),
        start_time=(now - timedelta(minutes=5)).time().replace(microsecond=0),
        late_time=(now + timedelta(minutes=10)).time().replace(microsecond=0),
        end_time=(now + timedelta(hours=2)).time().replace(microsecond=0),
        room=class_group.room,
    )

    session = academic_service.generate_session_from_schedule(db, schedule.id)

    return {
        "class_group": class_group,
        "subject": iot_subject,
        "schedule": schedule,
        "session": session,
        "students": students,
    }


def reset_demo_data(db: Session) -> dict:
    academic_service.ensure_academic_schema(db)

    deleted_attendance = db.query(Attendance).delete(synchronize_session=False)
    deleted_behavior = db.query(BehaviorEvent).delete(synchronize_session=False)
    deleted_sessions = db.query(ClassSession).delete(synchronize_session=False)
    deleted_enrollments = db.query(Enrollment).delete(synchronize_session=False)
    deleted_schedules = db.query(WeeklySchedule).delete(synchronize_session=False)
    deleted_classes = db.query(ClassGroup).delete(synchronize_session=False)
    deleted_subjects = db.query(Subject).delete(synchronize_session=False)

    db.commit()

    students = _reset_demo_students(db)
    demo = _create_demo_academics(db)
    session = demo["session"]

    return {
        "ok": True,
        "message": "Demo data reset successfully with academic schedule.",
        "deleted_attendance": deleted_attendance,
        "deleted_behavior_events": deleted_behavior,
        "deleted_sessions": deleted_sessions,
        "deleted_enrollments": deleted_enrollments,
        "deleted_schedules": deleted_schedules,
        "deleted_classes": deleted_classes,
        "deleted_subjects": deleted_subjects,
        "students_count": len(students),
        "class_code": demo["class_group"].class_code,
        "subject": demo["subject"].subject_name,
        "new_session_id": session.id,
        "new_session_title": session.title,
        "start_time": session.start_time,
        "late_time": session.late_time,
        "close_time": session.close_time,
        "source": session.source,
    }
