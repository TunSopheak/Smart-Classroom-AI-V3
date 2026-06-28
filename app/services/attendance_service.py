from datetime import datetime
import hashlib

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.class_session import ClassSession
from app.services import student_service, session_service


def status_for_time(detected_at: datetime, session: ClassSession) -> str:
    if detected_at <= session.late_time:
        return "present"
    if detected_at <= session.close_time:
        return "late"
    return "late"


def get_existing(db: Session, student_id: int, session_id: int):
    return (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id, Attendance.session_id == session_id)
        .first()
    )


def mark_face_attendance(
    db: Session,
    student_code: str,
    confidence: float | None = None,
    session_id: int | None = None,
    detected_at: datetime | None = None,
):
    detected_at = detected_at or datetime.now()

    session = (
        db.query(ClassSession).filter(ClassSession.id == session_id).first()
        if session_id
        else session_service.get_active_session(db)
    )
    if not session:
        return {"ok": False, "reason": "no_active_session"}

    student = student_service.get_by_code(db, student_code)
    if not student:
        return {"ok": False, "reason": "student_not_found", "student_code": student_code}

    existing = get_existing(db, student.id, session.id)
    if existing:
        return {
            "ok": True,
            "duplicate": True,
            "student_code": student.student_code,
            "student_name": student.full_name,
            "status": existing.status,
            "detected_time": existing.first_seen_time,
        }

    status = status_for_time(detected_at, session)
    attendance = Attendance(
        student_id=student.id,
        session_id=session.id,
        first_seen_time=detected_at,
        status=status,
        method="face",
        confidence=confidence,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "ok": True,
        "duplicate": False,
        "student_code": student.student_code,
        "student_name": student.full_name,
        "status": status,
        "detected_time": detected_at,
        "confidence": confidence,
    }


def create_absent_for_missing(db: Session, session: ClassSession) -> int:
    created = 0
    students = student_service.get_active_students(db)

    for student in students:
        if get_existing(db, student.id, session.id):
            continue

        db.add(
            Attendance(
                student_id=student.id,
                session_id=session.id,
                first_seen_time=None,
                status="absent",
                method="manual",
                confidence=None,
            )
        )
        created += 1

    db.commit()
    return created


def attendance_summary(db: Session, session_id: int | None = None):
    session = (
        db.query(ClassSession).filter(ClassSession.id == session_id).first()
        if session_id
        else session_service.get_active_session(db)
    )

    total_students = len(student_service.get_active_students(db))
    summary = {
        "total_students": total_students,
        "present": 0,
        "late": 0,
        "absent": 0,
        "permission": 0,
        "session": session,
    }

    if not session:
        return summary

    records = db.query(Attendance).filter(Attendance.session_id == session.id).all()
    for record in records:
        if record.status in summary:
            summary[record.status] += 1

    return summary


def recent_attendance(db: Session, limit: int = 10):
    return db.query(Attendance).order_by(Attendance.created_at.desc()).limit(limit).all()


def qr_token_for_student(student) -> str:
    raw = f"{student.id}:{student.student_code}:{student.created_at.isoformat()}:smart-classroom-ai-v3-student-card"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def validate_student_qr_token(student, token: str) -> bool:
    return token == qr_token_for_student(student)


def mark_qr_attendance(
    db: Session,
    student_code: str,
    token: str,
    detected_at: datetime | None = None,
):
    detected_at = detected_at or datetime.now()

    session = session_service.get_active_session(db)
    if not session:
        return {"ok": False, "reason": "no_active_session"}

    if detected_at > session.close_time:
        return {"ok": False, "reason": "session_closed"}

    student = student_service.get_by_code(db, student_code.strip())
    if not student:
        return {"ok": False, "reason": "student_not_found", "student_code": student_code}

    if student.status != "active":
        return {
            "ok": False,
            "reason": "inactive_student",
            "student_code": student.student_code,
            "student_name": student.full_name,
        }

    if not validate_student_qr_token(student, token):
        return {
            "ok": False,
            "reason": "invalid_student_qr",
            "student_code": student.student_code,
            "student_name": student.full_name,
        }

    existing = get_existing(db, student.id, session.id)
    if existing:
        return {
            "ok": True,
            "duplicate": True,
            "student_code": student.student_code,
            "student_name": student.full_name,
            "status": existing.status,
            "method": existing.method,
            "detected_time": existing.first_seen_time,
            "session_title": session.title,
        }

    status = status_for_time(detected_at, session)
    attendance = Attendance(
        student_id=student.id,
        session_id=session.id,
        first_seen_time=detected_at,
        status=status,
        method="qr",
        confidence=None,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return {
        "ok": True,
        "duplicate": False,
        "student_code": student.student_code,
        "student_name": student.full_name,
        "status": status,
        "method": "qr",
        "detected_time": detected_at,
        "session_title": session.title,
    }
