import json
from pathlib import Path

import cv2
import numpy as np

from app.core.config import FACE_DATASET_DIR, FACE_LABELS_PATH, FACE_MODEL_PATH


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _student_code_from_folder(folder: Path) -> str:
    return folder.name.split("_", 1)[0].strip()


def dataset_counts() -> dict[str, int]:
    FACE_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for folder in FACE_DATASET_DIR.iterdir():
        if not folder.is_dir():
            continue

        student_code = _student_code_from_folder(folder)
        count = sum(1 for file in folder.iterdir() if file.suffix.lower() in IMAGE_EXTENSIONS)
        counts[student_code] = count

    return counts


def model_status() -> dict:
    counts = dataset_counts()
    total_images = sum(counts.values())

    status = {
        "trained": FACE_MODEL_PATH.exists() and FACE_LABELS_PATH.exists(),
        "model_path": str(FACE_MODEL_PATH),
        "labels_path": str(FACE_LABELS_PATH),
        "total_dataset_images": total_images,
        "student_counts": counts,
        "labels": {},
    }

    if FACE_LABELS_PATH.exists():
        try:
            status["labels"] = json.loads(FACE_LABELS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status["labels"] = {}

    return status


def train_lbph_model() -> dict:
    FACE_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    FACE_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    images: list[np.ndarray] = []
    labels: list[int] = []
    label_to_student_code: dict[int, str] = {}
    student_code_to_label: dict[str, int] = {}

    next_label = 0

    for folder in sorted(FACE_DATASET_DIR.iterdir()):
        if not folder.is_dir():
            continue

        student_code = _student_code_from_folder(folder)
        if not student_code:
            continue

        if student_code not in student_code_to_label:
            student_code_to_label[student_code] = next_label
            label_to_student_code[next_label] = student_code
            next_label += 1

        numeric_label = student_code_to_label[student_code]

        for image_path in sorted(folder.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue

            image = cv2.resize(image, (200, 200))
            images.append(image)
            labels.append(numeric_label)

    if not images:
        return {
            "ok": False,
            "message": "No training images found. Capture face dataset first.",
            "trained_images": 0,
            "trained_students": 0,
        }

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels, dtype=np.int32))
    recognizer.save(str(FACE_MODEL_PATH))

    labels_payload = {
        "label_to_student_code": {str(label): code for label, code in label_to_student_code.items()},
        "student_code_to_label": {code: label for code, label in student_code_to_label.items()},
        "trained_images": len(images),
        "trained_students": len(student_code_to_label),
    }

    FACE_LABELS_PATH.write_text(json.dumps(labels_payload, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "message": "Face model trained successfully.",
        "trained_images": len(images),
        "trained_students": len(student_code_to_label),
        "model_path": str(FACE_MODEL_PATH),
        "labels_path": str(FACE_LABELS_PATH),
    }
