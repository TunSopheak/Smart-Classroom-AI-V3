from __future__ import annotations

import base64
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.behavior_event import BehaviorEvent
from app.services import session_service

SNAPSHOT_ROOT = Path("media") / "snapshots"


def ensure_snapshot_folder():
    SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)


def list_behavior_events(db: Session):
    return db.query(BehaviorEvent).order_by(BehaviorEvent.detected_at.desc()).all()


def behavior_summary(db: Session) -> dict:
    total = db.query(BehaviorEvent).count()
    alerts = db.query(BehaviorEvent).filter(BehaviorEvent.severity == "alert").count()
    warnings = db.query(BehaviorEvent).filter(BehaviorEvent.severity == "warning").count()

    return {
        "total": total,
        "alerts": alerts,
        "warnings": warnings,
    }


def _decode_frame(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    raw = base64.b64decode(image_data)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Invalid image data for snapshot.")

    return frame


def _center(box: dict) -> tuple[float, float]:
    return (box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)


def _contains(box: dict, point: tuple[float, float]) -> bool:
    px, py = point
    return box["x"] <= px <= box["x"] + box["w"] and box["y"] <= py <= box["y"] + box["h"]


def _match_student_for_alert(alert: dict, recognitions: list[dict]) -> dict | None:
    alert_box = alert.get("box")
    if not alert_box:
        return None

    for item in recognitions:
        if not item.get("recognized") or not item.get("box"):
            continue

        face_center = _center(item["box"])
        if _contains(alert_box, face_center):
            return item

    return None


def _draw_box(frame, box: dict, label: str, color: tuple[int, int, int], thickness: int = 3):
    x, y, w, h = int(box["x"]), int(box["y"]), int(box["w"]), int(box["h"])
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)

    label_y = max(0, y - 28)
    cv2.rectangle(frame, (x, label_y), (x + max(220, len(label) * 11), label_y + 28), color, -1)
    cv2.putText(
        frame,
        label,
        (x + 8, label_y + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def _save_snapshot(
    image_data: str,
    session_id: int,
    alert: dict,
    student_name: str,
) -> str:
    ensure_snapshot_folder()

    frame = _decode_frame(image_data)

    # OpenCV color format is BGR.
    _draw_box(
        frame,
        alert["box"],
        f"{student_name} | {alert.get('label', 'Alert')}",
        (0, 0, 255),
        4,
    )

    object_box = alert.get("object_box")
    if object_box:
        _draw_box(frame, object_box, "Object Candidate", (0, 165, 255), 2)

    session_folder = SNAPSHOT_ROOT / f"session_{session_id}"
    session_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{alert.get('event_type', 'behavior_alert')}_{timestamp}.jpg"
    path = session_folder / filename

    cv2.imwrite(str(path), frame)

    return "/" + path.as_posix()


def _recent_duplicate_exists(
    db: Session,
    session_id: int | None,
    event_type: str,
    message: str,
    seconds: int = 25,
) -> bool:
    cutoff = datetime.now() - timedelta(seconds=seconds)

    return (
        db.query(BehaviorEvent)
        .filter(
            BehaviorEvent.session_id == session_id,
            BehaviorEvent.event_type == event_type,
            BehaviorEvent.message == message,
            BehaviorEvent.detected_at >= cutoff,
        )
        .first()
        is not None
    )


def create_alert_events_from_frame(
    db: Session,
    image_data: str,
    recognition_result: dict,
    behavior_result: dict,
) -> list[dict]:
    session = session_service.get_active_session(db)
    session_id = session.id if session else None

    recognitions = recognition_result.get("recognitions", [])
    alert_candidates = behavior_result.get("alert_candidates", [])

    saved_events = []

    for alert in alert_candidates:
        matched_student = _match_student_for_alert(alert, recognitions)

        student_name = "Unknown student"
        student_code = None

        if matched_student:
            student_name = (
                matched_student.get("student_display_name")
                or matched_student.get("student_name")
                or matched_student.get("student_code")
                or "Recognized student"
            )
            student_code = matched_student.get("student_code")

        event_type = alert.get("event_type", "behavior_alert")
        severity = alert.get("severity", "alert")
        message = f"{student_name} - {alert.get('message', 'Behavior alert candidate detected.')}"

        if _recent_duplicate_exists(db, session_id, event_type, message):
            alert["student_name"] = student_name
            alert["student_code"] = student_code
            alert["message"] = message
            continue

        snapshot_path = _save_snapshot(
            image_data=image_data,
            session_id=session_id or 0,
            alert=alert,
            student_name=student_name,
        )

        event = BehaviorEvent(
            session_id=session_id,
            event_type=event_type,
            severity=severity,
            message=message,
            confidence=alert.get("confidence"),
            snapshot_path=snapshot_path,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        alert["student_name"] = student_name
        alert["student_code"] = student_code
        alert["message"] = message
        alert["snapshot_path"] = snapshot_path

        saved_events.append(
            {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "message": event.message,
                "confidence": event.confidence,
                "snapshot_path": event.snapshot_path,
                "detected_at": event.detected_at,
                "student_name": student_name,
                "student_code": student_code,
            }
        )

    return saved_events
