import base64
import re
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.ai import face_training
from app.core.config import FACE_DATASET_DIR
from app.services import student_service


def _safe_text(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", value)
    return cleaned or "Student"


def dataset_folder_for_student(student) -> Path:
    folder_name = f"{student.student_code}_{_safe_text(student.first_name)}{_safe_text(student.last_name)}"
    return FACE_DATASET_DIR / folder_name


def get_dataset_counts_for_students(db: Session) -> list[dict]:
    counts = face_training.dataset_counts()
    students = student_service.get_students(db)

    result = []
    for student in students:
        result.append(
            {
                "student_code": student.student_code,
                "student_name": student.full_name,
                "image_count": counts.get(student.student_code, 0),
                "folder": str(dataset_folder_for_student(student)),
            }
        )

    return result


def get_training_status(db: Session) -> dict:
    status = face_training.model_status()
    status["students"] = get_dataset_counts_for_students(db)
    return status


def _decode_base64_image(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    raw = base64.b64decode(image_data)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Invalid image data.")

    return frame


def _largest_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(40, 40),
    )

    if len(faces) == 0:
        return None

    return max(faces, key=lambda box: box[2] * box[3])


def save_face_capture(db: Session, student_code: str, image_data: str) -> dict:
    student = student_service.get_by_code(db, student_code)
    if not student:
        return {"ok": False, "message": f"Student not found: {student_code}"}

    frame = _decode_base64_image(image_data)
    face_box = _largest_face(frame)

    if face_box is None:
        return {
            "ok": False,
            "message": "No clear face detected. Please face the camera and try again.",
        }

    x, y, w, h = face_box
    face = frame[y : y + h, x : x + w]
    face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    face_gray = cv2.resize(face_gray, (200, 200))

    folder = dataset_folder_for_student(student)
    folder.mkdir(parents=True, exist_ok=True)

    existing_images = sorted(folder.glob("*.jpg"))
    next_number = len(existing_images) + 1
    image_path = folder / f"{next_number:03d}.jpg"

    saved = cv2.imwrite(str(image_path), face_gray)
    if not saved:
        return {"ok": False, "message": "Failed to save face image."}

    return {
        "ok": True,
        "message": "Face image captured successfully.",
        "student_code": student.student_code,
        "student_name": student.full_name,
        "image_path": str(image_path),
        "image_count": next_number,
    }


def train_model() -> dict:
    return face_training.train_lbph_model()

