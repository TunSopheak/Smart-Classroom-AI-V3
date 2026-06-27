from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "smart_classroom_ai_v3.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

APP_NAME = "Smart Classroom AI V3"

FACE_DATASET_DIR = BASE_DIR / "models" / "face_dataset"
FACE_MODEL_PATH = BASE_DIR / "models" / "face_model.yml"
FACE_LABELS_PATH = BASE_DIR / "models" / "face_labels.json"

# LBPH distance: lower is better. Smaller value = stricter recognition.
# 85 was too loose and caused false names in crowded classroom.
FACE_RECOGNITION_THRESHOLD = 50.0
FACE_RECOGNITION_MIN_CONFIDENCE = 50.0
