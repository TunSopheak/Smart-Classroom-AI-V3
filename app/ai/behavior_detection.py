import base64

import cv2
import numpy as np


def _decode_base64_frame(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    raw = base64.b64decode(image_data)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Invalid image data.")

    return frame


def _detect_faces(gray_frame):
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    return face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(40, 40),
    )


def _estimate_person_box_from_face(face_box, frame_width: int, frame_height: int) -> dict:
    x, y, w, h = face_box

    # Estimate upper-body/student candidate box from the face position.
    # This is lightweight for demo. Real full-body detection can be added later.
    body_w = int(w * 2.4)
    body_h = int(h * 4.2)

    body_x = int(x - (body_w - w) / 2)
    body_y = int(y - h * 0.25)

    body_x = max(0, body_x)
    body_y = max(0, body_y)

    if body_x + body_w > frame_width:
        body_w = frame_width - body_x

    if body_y + body_h > frame_height:
        body_h = frame_height - body_y

    return {
        "x": int(body_x),
        "y": int(body_y),
        "w": int(body_w),
        "h": int(body_h),
    }


def analyze_behavior_from_image_data(image_data: str) -> dict:
    frame = _decode_base64_frame(image_data)
    height, width = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _detect_faces(gray)

    person_candidates = []
    face_candidates = []

    for face in faces:
        x, y, w, h = face

        face_candidates.append(
            {
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            }
        )

        person_candidates.append(
            _estimate_person_box_from_face(face, frame_width=width, frame_height=height)
        )

    person_count = len(person_candidates)
    face_count = len(face_candidates)

    summary = "No person detected"
    if person_count == 1:
        summary = "One student/person candidate detected"
    elif person_count > 1:
        summary = f"{person_count} student/person candidates detected"

    return {
        "ok": True,
        "summary": summary,
        "person_count": person_count,
        "face_count": face_count,
        "phone_candidates": 0,
        "looking_away_candidates": 0,
        "head_down_candidates": 0,
        "person_candidates": person_candidates,
        "face_candidates": face_candidates,
        "events": [
            {
                "event_type": "person_count",
                "severity": "info",
                "message": summary,
                "confidence": None,
            }
        ],
    }
