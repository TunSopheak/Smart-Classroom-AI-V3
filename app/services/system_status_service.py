from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai import face_training
from app.models.class_session import ClassSession
from app.models.student import Student


def get_system_status(db: Session) -> dict:
    database_ok = True
    database_message = "Database connected"

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database_ok = False
        database_message = f"Database error: {type(exc).__name__}: {exc}"

    students_count = db.query(Student).count()

    active_session = (
        db.query(ClassSession)
        .filter(ClassSession.is_active == True)
        .order_by(ClassSession.start_time.desc())
        .first()
    )

    face_status = face_training.model_status()

    return {
        "app_name": "Smart Classroom AI V3",
        "database_ok": database_ok,
        "database_message": database_message,
        "students_count": students_count,
        "active_session": active_session,
        "face_model_trained": face_status.get("trained", False),
        "total_dataset_images": face_status.get("total_dataset_images", 0),
        "trained_students": len(face_status.get("student_counts", {})),
        "camera_mode": "Computer webcam demo",
        "raspberry_pi_ready": True,
        "raspberry_pi_note": "Raspberry Pi 5 can be used later as camera/snapshot source. Current demo uses computer webcam for reliability.",
        "features": [
            {"name": "AI Training Center", "status": "Ready"},
            {"name": "Face Recognition Attendance", "status": "Ready"},
            {"name": "Auto Attendance", "status": "Ready"},
            {"name": "Demo Reset", "status": "Ready"},
            {"name": "Behavior Monitoring Candidate Review", "status": "Ready"},
            {"name": "Raspberry Pi 5 Integration", "status": "Prepared"},
        ],
    }
