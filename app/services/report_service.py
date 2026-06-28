from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.behavior_event import BehaviorEvent
from app.services import attendance_service, session_service


def attendance_report(db: Session):
    summary = attendance_service.attendance_summary(db)
    session = summary.get("session")

    method_counts = {
        "face": 0,
        "qr": 0,
        "manual": 0,
    }

    records = []

    if session:
        records = (
            db.query(Attendance)
            .filter(Attendance.session_id == session.id)
            .order_by(Attendance.created_at.desc())
            .all()
        )

        for record in records:
            if record.method in method_counts:
                method_counts[record.method] += 1
            else:
                method_counts[record.method] = method_counts.get(record.method, 0) + 1

    return {
        "summary": summary,
        "session": session,
        "method_counts": method_counts,
        "records": records,
    }


def ai_event_report(db: Session, limit: int = 80):
    events = (
        db.query(BehaviorEvent)
        .order_by(BehaviorEvent.detected_at.desc())
        .limit(limit)
        .all()
    )

    summary = {
        "total": len(events),
        "alerts": 0,
        "warnings": 0,
        "info": 0,
        "snapshots": 0,
    }

    for event in events:
        if event.severity == "alert":
            summary["alerts"] += 1
        elif event.severity == "warning":
            summary["warnings"] += 1
        else:
            summary["info"] += 1

        if event.snapshot_path:
            summary["snapshots"] += 1

    alert_events = [event for event in events if event.severity == "alert"]

    return {
        "summary": summary,
        "events": events,
        "alert_events": alert_events,
    }
