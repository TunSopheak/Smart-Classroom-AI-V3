from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.behavior_event import BehaviorEvent
from app.models.class_session import ClassSession


def create_fresh_demo_session(db: Session) -> ClassSession:
    now = datetime.now()

    session = ClassSession(
        title="Fresh AI Attendance Demo",
        class_name="M4-Y3",
        subject="IoT Project",
        room="Demo Room",
        start_time=now,
        late_time=now + timedelta(minutes=10),
        close_time=now + timedelta(hours=2),
        is_active=True,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def reset_demo_data(db: Session) -> dict:
    deleted_attendance = db.query(Attendance).delete(synchronize_session=False)
    deleted_behavior = db.query(BehaviorEvent).delete(synchronize_session=False)
    deleted_sessions = db.query(ClassSession).delete(synchronize_session=False)

    db.commit()

    session = create_fresh_demo_session(db)

    return {
        "ok": True,
        "message": "Demo data reset successfully.",
        "deleted_attendance": deleted_attendance,
        "deleted_behavior_events": deleted_behavior,
        "deleted_sessions": deleted_sessions,
        "new_session_id": session.id,
        "new_session_title": session.title,
        "start_time": session.start_time,
        "late_time": session.late_time,
        "close_time": session.close_time,
    }
