import base64
import json

import cv2
import numpy as np

from app.core.config import FACE_LABELS_PATH, FACE_MODEL_PATH, FACE_RECOGNITION_THRESHOLD


def confidence_from_distance(distance: float) -> float:
    confidence = 100.0 - float(distance)
    if confidence < 0:
        confidence = 0.0
    if confidence > 100:
        confidence = 100.0
    return round(confidence, 2)


def model_ready() -> bool:
    return FACE_MODEL_PATH.exists() and FACE_LABELS_PATH.exists()


def _decode_base64_frame(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    raw = base64.b64decode(image_data)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Invalid image data.")

    return frame


def _load_label_map() -> dict[int, str]:
    if not FACE_LABELS_PATH.exists():
        return {}

    payload = json.loads(FACE_LABELS_PATH.read_text(encoding="utf-8"))
    label_to_student_code = payload.get("label_to_student_code", {})

    result = {}
    for label, student_code in label_to_student_code.items():
        result[int(label)] = student_code

    return result


def _detect_faces(gray_frame):
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(40, 40),
    )

    return faces


def recognize_faces_from_image_data(image_data: str) -> dict:
    if not model_ready():
        return {
            "ok": False,
            "reason": "model_not_trained",
            "message": "Face model is not trained yet. Capture dataset and train model first.",
            "recognitions": [],
            "face_count": 0,
        }

    frame = _decode_base64_frame(image_data)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _detect_faces(gray)

    if len(faces) == 0:
        return {
            "ok": True,
            "message": "No face detected.",
            "recognitions": [],
            "face_count": 0,
        }

    label_map = _load_label_map()

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(FACE_MODEL_PATH))

    recognitions = []

    for x, y, w, h in faces:
        face = gray[y : y + h, x : x + w]
        face = cv2.resize(face, (200, 200))

        label, distance = recognizer.predict(face)
        student_code = label_map.get(int(label))
        is_known = student_code is not None and float(distance) <= FACE_RECOGNITION_THRESHOLD

        recognitions.append(
            {
                "recognized": bool(is_known),
                "student_code": student_code if is_known else None,
                "distance": round(float(distance), 2),
                "confidence": confidence_from_distance(distance),
                "threshold": FACE_RECOGNITION_THRESHOLD,
                "box": {
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                },
            }
        )

    recognized_count = sum(1 for item in recognitions if item["recognized"])

    return {
        "ok": True,
        "message": f"Detected {len(recognitions)} face(s), recognized {recognized_count}.",
        "recognitions": recognitions,
        "face_count": len(recognitions),
        "recognized_count": recognized_count,
    }

