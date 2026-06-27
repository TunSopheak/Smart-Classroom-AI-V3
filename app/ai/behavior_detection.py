from __future__ import annotations

import base64

import cv2
import numpy as np

from app.ai.yolo_detector import get_yolo_detector


PHONE_LABELS = {"phone", "cell phone", "mobile phone", "smartphone", "telephone"}


def _decode_base64_bytes(image_data: str) -> bytes:
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    return base64.b64decode(image_data)


def _decode_frame(image_data: str):
    raw = _decode_base64_bytes(image_data)
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Invalid image data.")

    return raw, frame


def _normalize_label(label: object) -> str:
    return " ".join(
        str(label or "")
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def _is_phone_label(label: object) -> bool:
    normalized = _normalize_label(label)
    compact = normalized.replace(" ", "")
    return normalized in PHONE_LABELS or "phone" in normalized or compact in {"cellphone", "mobilephone"}


def _xyxy_to_xywh(box: list[float]) -> dict:
    x1, y1, x2, y2 = box
    return {
        "x": int(round(x1)),
        "y": int(round(y1)),
        "w": int(round(x2 - x1)),
        "h": int(round(y2 - y1)),
    }


def _xywh_to_xyxy(box: dict) -> list[float]:
    return [
        float(box["x"]),
        float(box["y"]),
        float(box["x"] + box["w"]),
        float(box["y"] + box["h"]),
    ]


def _box_area(box: list[float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _intersection_area(a: list[float], b: list[float]) -> float:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    return max(0.0, right - left) * max(0.0, bottom - top)


def _center(box: list[float]) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _center_inside(inner_box: list[float], outer_box: list[float]) -> bool:
    cx, cy = _center(inner_box)
    return outer_box[0] <= cx <= outer_box[2] and outer_box[1] <= cy <= outer_box[3]


def _phone_person_score(phone_box: list[float], person_box: list[float], phone_confidence: float) -> float:
    phone_area = _box_area(phone_box)
    person_area = _box_area(person_box)

    if phone_area <= 0 or person_area <= 0:
        return 0.0

    overlap = _intersection_area(phone_box, person_box)
    overlap_ratio = overlap / phone_area
    area_ratio = phone_area / person_area

    cx, cy = _center(phone_box)
    rel_y = (cy - person_box[1]) / max(1.0, person_box[3] - person_box[1])

    center_inside = _center_inside(phone_box, person_box)

    if rel_y < 0.22:
        return 0.0

    if area_ratio < 0.003 or area_ratio > 0.25:
        return 0.0

    if not center_inside and overlap_ratio < 0.10:
        return 0.0

    if phone_confidence < 0.18:
        return 0.0

    return overlap_ratio + (0.2 if center_inside else 0.0) + phone_confidence


def _detect_phone_fallback(frame, person_box_xywh: dict) -> dict | None:
    """Webcam fallback when YOLO misses a phone.

    Final tuning:
    - reject skin/hand regions
    - prefer vertical phone-like rectangles
    - require dark/edge structure
    - search only inside person area
    """

    height, width = frame.shape[:2]

    px = max(0, person_box_xywh["x"])
    py = max(0, person_box_xywh["y"])
    pw = max(1, person_box_xywh["w"])
    ph = max(1, person_box_xywh["h"])

    # Search lower/middle person area. This catches phone in hand/chest area.
    roi_y = py + int(ph * 0.20)
    roi_h = min(height - roi_y, int(ph * 0.78))
    roi_x = px
    roi_w = min(width - roi_x, pw)

    if roi_h <= 40 or roi_w <= 40:
        return None

    roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect phone body/screen edges.
    edges = cv2.Canny(blurred, 35, 120)

    # Detect dark phone body / black screen / black phone border.
    dark_mask = cv2.inRange(blurred, 0, 135)

    combined = cv2.bitwise_or(edges, dark_mask)

    kernel = np.ones((3, 3), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def local_skin_ratio(bgr_crop) -> float:
        if bgr_crop is None or bgr_crop.size == 0:
            return 0.0

        hsv = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2HSV)

        lower_1 = np.array([0, 25, 45], dtype=np.uint8)
        upper_1 = np.array([30, 190, 255], dtype=np.uint8)

        lower_2 = np.array([160, 25, 45], dtype=np.uint8)
        upper_2 = np.array([180, 190, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower_1, upper_1) | cv2.inRange(hsv, lower_2, upper_2)
        return float(cv2.countNonZero(mask)) / float(mask.size)

    best = None
    best_score = 0.0
    person_area = max(1, pw * ph)
    roi_area = max(1, roi_w * roi_h)

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < 650 or area > roi_area * 0.18:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        rect_area = max(1, w * h)
        aspect = w / float(h)
        extent = area / rect_area

        # Phone is usually vertical in our demo. This rejects most hand/palm regions.
        if not (0.25 <= aspect <= 1.15):
            continue

        if h < 55 or w < 24:
            continue

        if extent < 0.14:
            continue

        if w > pw * 0.55 or h > ph * 0.62:
            continue

        abs_box = {
            "x": int(roi_x + x),
            "y": int(roi_y + y),
            "w": int(w),
            "h": int(h),
        }

        phone_area = _box_area(_xywh_to_xyxy(abs_box))
        area_ratio = phone_area / person_area

        if area_ratio < 0.003 or area_ratio > 0.20:
            continue

        crop_bgr = roi[y:y + h, x:x + w]
        crop_gray = gray[y:y + h, x:x + w]
        crop_edges = edges[y:y + h, x:x + w]

        skin = local_skin_ratio(crop_bgr)
        dark_ratio = float(cv2.countNonZero(cv2.inRange(crop_gray, 0, 145))) / float(crop_gray.size)
        edge_ratio = float(cv2.countNonZero(crop_edges)) / float(crop_edges.size)
        mean_value = float(np.mean(crop_gray))

        # Critical: reject hand/skin false positives.
        if skin > 0.28:
            continue

        # Must look like phone/screen: dark body or strong rectangular edges.
        if dark_ratio < 0.18 and edge_ratio < 0.045:
            continue

        # Bright wall/skin/object with weak edges should not pass.
        if mean_value > 175 and edge_ratio < 0.08:
            continue

        vertical_bonus = 0.18 if h > w * 1.45 else 0.0
        score = (dark_ratio * 0.42) + (edge_ratio * 3.2) + (area_ratio * 1.3) + vertical_bonus

        if score > best_score:
            best_score = score
            best = abs_box

    # Higher threshold prevents hand false positive.
    if best is None or best_score < 0.34:
        return None

    best["confidence"] = int(min(88, max(50, best_score * 100)))
    best["source"] = "opencv_phone_fallback"
    return best




def _detect_faces_for_fallback(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    return face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(65, 65),
    )


def _estimate_person_box_from_face(face_box, frame_width: int, frame_height: int) -> dict:
    x, y, w, h = face_box

    body_w = int(w * 2.35)
    body_h = int(h * 5.0)

    body_x = int(x - (body_w - w) / 2)
    body_y = int(y - h * 0.12)

    body_x = max(0, body_x)
    body_y = max(0, body_y)

    if body_x + body_w > frame_width:
        body_w = frame_width - body_x

    if body_y + body_h > frame_height:
        body_h = frame_height - body_y

    return {
        "x": int(body_x),
        "y": int(body_y),
        "w": int(max(1, body_w)),
        "h": int(max(1, body_h)),
    }


def _fallback_person_detection(frame, reason: str) -> dict:
    height, width = frame.shape[:2]
    faces = _detect_faces_for_fallback(frame)

    person_candidates = []
    face_candidates = []

    for face in faces:
        x, y, w, h = face
        face_box = {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
        face_candidates.append(face_box)
        person_candidates.append(_estimate_person_box_from_face(face, width, height))

    return _build_result(
        person_candidates=person_candidates,
        phones=[],
        books=[],
        frame=frame,
        model_source="haar_fallback",
        model_message=reason,
    )


def _build_result(person_candidates, phones, books, frame, model_source, model_message):
    phone_candidate_boxes = []
    book_candidate_boxes = []
    alert_candidates = []
    warning_candidates = []

    used_phones = set()

    for index, person_box in enumerate(person_candidates, start=1):
        person_xyxy = _xywh_to_xyxy(person_box)

        best_phone_index = None
        best_phone = None
        best_score = 0.0

        for phone_index, phone in enumerate(phones):
            if phone_index in used_phones:
                continue

            score = _phone_person_score(
                phone_box=phone["xyxy"],
                person_box=person_xyxy,
                phone_confidence=float(phone.get("confidence") or 0),
            )

            if score > best_score:
                best_score = score
                best_phone_index = phone_index
                best_phone = phone

        if best_phone is not None and best_score > 0:
            used_phones.add(best_phone_index)

            confidence = int(round(float(best_phone.get("confidence") or 0) * 100))
            phone_box = best_phone["xywh"]
            phone_box["confidence"] = confidence
            phone_box["source"] = "yolo"

        else:
            phone_box = _detect_phone_fallback(frame, person_box)
            confidence = phone_box.get("confidence", 0) if phone_box else 0

        if phone_box:
            phone_candidate_boxes.append(phone_box)

            alert_candidates.append(
                {
                    "event_type": "phone_use_candidate",
                    "severity": "alert",
                    "label": "Phone-use Alert",
                    "message": "Phone-like object detected near this person candidate. Teacher review required.",
                    "box": person_box,
                    "object_box": phone_box,
                    "confidence": confidence,
                    "track_id": index,
                    "model_source": phone_box.get("source", "yolo_or_fallback"),
                }
            )

    for book in books:
        confidence = int(round(float(book.get("confidence") or 0) * 100))
        box = book["xywh"]
        box["confidence"] = confidence

        book_candidate_boxes.append(box)
        warning_candidates.append(
            {
                "event_type": "book_object_candidate",
                "severity": "warning",
                "label": "Book/Object Candidate",
                "message": "Book/object candidate detected. Teacher review optional.",
                "box": box,
                "confidence": confidence,
                "model_source": model_source,
            }
        )

    person_count = len(person_candidates)
    phone_count = len(phone_candidate_boxes)
    book_count = len(book_candidate_boxes)

    summary = "No person detected"
    if phone_count > 0:
        summary = f"{phone_count} phone-use candidate(s) detected"
    elif person_count == 1:
        summary = "One person candidate detected"
    elif person_count > 1:
        summary = f"{person_count} person candidates detected"

    return {
        "ok": True,
        "summary": summary,
        "model_source": model_source,
        "model_message": model_message,
        "person_count": person_count,
        "face_count": 0,
        "phone_candidates": phone_count,
        "book_candidates": book_count,
        "looking_away_candidates": 0,
        "head_down_candidates": 0,
        "person_candidates": person_candidates,
        "face_candidates": [],
        "phone_candidate_boxes": phone_candidate_boxes,
        "book_candidate_boxes": book_candidate_boxes,
        "alert_candidates": alert_candidates,
        "warning_candidates": warning_candidates,
        "events": [
            {
                "event_type": "person_count",
                "severity": "info",
                "message": summary,
                "confidence": None,
            }
        ],
    }


def analyze_behavior_from_image_data(image_data: str) -> dict:
    raw, frame = _decode_frame(image_data)
    yolo_result = get_yolo_detector().analyze(raw)

    if not yolo_result.get("available"):
        return _fallback_person_detection(frame, yolo_result.get("message", "YOLO unavailable."))

    detections = yolo_result.get("detections", [])

    persons = []
    phones = []
    books = []

    for detection in detections:
        label = _normalize_label(detection.get("label"))
        box = detection.get("box")

        if not isinstance(box, list) or len(box) != 4:
            continue

        confidence = float(detection.get("confidence") or 0)
        xyxy = [float(value) for value in box]

        item = {
            "label": label,
            "confidence": confidence,
            "xyxy": xyxy,
            "xywh": _xyxy_to_xywh(xyxy),
        }

        if label == "person":
            persons.append(item)
        elif _is_phone_label(label):
            phones.append(item)
        elif label == "book":
            books.append(item)

    persons.sort(key=lambda item: item["xyxy"][0])
    person_candidates = [item["xywh"] for item in persons]

    return _build_result(
        person_candidates=person_candidates,
        phones=phones,
        books=books,
        frame=frame,
        model_source="yolov8n_plus_fallback",
        model_message=yolo_result.get("message", "YOLO object detection completed."),
    )
