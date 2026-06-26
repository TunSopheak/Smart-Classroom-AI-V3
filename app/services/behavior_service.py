from app.ai import behavior_detection


def placeholder_behavior_summary():
    return {
        "person_count": 0,
        "face_count": 0,
        "phone_candidates": 0,
        "looking_away_candidates": 0,
        "head_down_candidates": 0,
        "summary": "Not started",
        "person_candidates": [],
        "face_candidates": [],
        "events": [],
    }


def analyze_behavior_frame(image_data: str) -> dict:
    return behavior_detection.analyze_behavior_from_image_data(image_data)
