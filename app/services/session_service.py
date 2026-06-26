from datetime import datetime, time

from sqlalchemy.orm import Session

from app.models.class_session import ClassSession


def seed_default_session(db: Session) -> None:
    if db.query(ClassSession).count() > 0:
        return

    today = datetime.now().date()
    session = ClassSession(
        title="IoT Smart Classroom Demo",
        class_name="M4-Y3",
        subject="IoT Project",
        room="B108",
        start_time=datetime.combine(today, time(7, 30)),
        late_time=datetime.combine(today, time(7, 45)),
        close_time=datetime.combine(today, time(9, 0)),
        is_active=True,
    )
    db.add(session)
    db.commit()


def get_sessions(db: Session):
    return db.query(ClassSession).order_by(ClassSession.start_time.desc()).all()


def get_active_session(db: Session):
    return db.query(ClassSession).filter(ClassSession.is_active == True).first()


def start_session(db: Session, session_id: int):
    for session in db.query(ClassSession).all():
        session.is_active = session.id == session_id
    db.commit()
    return db.query(ClassSession).filter(ClassSession.id == session_id).first()


def close_session(db: Session, session_id: int):
    from app.services.attendance_service import create_absent_for_missing

    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        return None

    create_absent_for_missing(db, session)
    session.is_active = False
    db.commit()
    return session
