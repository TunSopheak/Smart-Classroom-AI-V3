from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.video_record import VideoRecord
from app.services import session_service

MEDIA_ROOT = Path("media")
RECORDINGS_ROOT = MEDIA_ROOT / "recordings"


def ensure_recordings_folder():
    RECORDINGS_ROOT.mkdir(parents=True, exist_ok=True)


def _safe_event_type(value: str) -> str:
    value = (value or "manual_clip").strip().lower().replace(" ", "_")
    return "".join(ch for ch in value if ch.isalnum() or ch in ["_", "-"]) or "manual_clip"


def list_video_records(db: Session):
    return db.query(VideoRecord).order_by(VideoRecord.recorded_at.desc()).all()


def count_video_records(db: Session) -> int:
    return db.query(VideoRecord).count()


def create_video_record(
    db: Session,
    session_id: int,
    event_type: str,
    title: str,
    note: str,
    video_path: str,
    file_name: str,
    mime_type: str = "video/webm",
    file_size_bytes: int = 0,
    duration_seconds: float = 0,
) -> VideoRecord:
    record = VideoRecord(
        session_id=session_id,
        event_type=_safe_event_type(event_type),
        title=title.strip(),
        note=(note or "").strip(),
        video_path=video_path,
        file_name=file_name,
        mime_type=mime_type or "video/webm",
        file_size_bytes=int(file_size_bytes or 0),
        duration_seconds=float(duration_seconds or 0),
        recorded_at=datetime.now(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_video_bytes_for_active_session(
    db: Session,
    content: bytes,
    original_filename: str,
    mime_type: str,
    event_type: str = "manual_clip",
    note: str = "",
    duration_seconds: float = 0,
) -> VideoRecord:
    ensure_recordings_folder()

    session = session_service.get_active_session(db)
    if not session:
        raise ValueError("No active session. Generate a session before saving video evidence.")

    event_type = _safe_event_type(event_type)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    ext = ".webm"
    if original_filename and "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()

    if ext not in [".webm", ".mp4", ".mov", ".mkv"]:
        ext = ".webm"

    session_folder = RECORDINGS_ROOT / f"session_{session.id}"
    session_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{timestamp}_{event_type}{ext}"
    file_path = session_folder / filename
    file_path.write_bytes(content)

    web_path = "/" + file_path.as_posix()

    title = f"{session.class_name} | {session.subject} | {event_type.replace('_', ' ').title()}"

    return create_video_record(
        db=db,
        session_id=session.id,
        event_type=event_type,
        title=title,
        note=note,
        video_path=web_path,
        file_name=filename,
        mime_type=mime_type or "video/webm",
        file_size_bytes=len(content),
        duration_seconds=duration_seconds,
    )


def video_summary(db: Session) -> dict:
    records = list_video_records(db)
    total_size = sum(item.file_size_bytes or 0 for item in records)

    return {
        "total_records": len(records),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
