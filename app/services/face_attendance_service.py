from sqlalchemy.orm import Session

from app.ai import face_recognition
from app.services import attendance_service, student_service


def analyze_frame_for_attendance(db: Session, image_data: str) -> dict:
    recognition_result = face_recognition.recognize_faces_from_image_data(image_data)

    if not recognition_result.get("ok"):
        return {
            "ok": False,
            "message": recognition_result.get("message", "Recognition failed."),
            "recognition": recognition_result,
            "attendance_results": [],
        }

    attendance_results = []

    for item in recognition_result.get("recognitions", []):
        student_code = item.get("student_code")

        if item.get("recognized") and student_code:
            student = student_service.get_by_code(db, student_code)
            if student:
                item["student_name"] = student.full_name
                item["student_display_name"] = student.full_name
            else:
                item["student_name"] = student_code
                item["student_display_name"] = student_code

        if not item.get("recognized") or not item.get("student_code"):
            attendance_results.append(
                {
                    "ok": False,
                    "reason": "unknown_face",
                    "message": "Unknown face. Attendance was not recorded.",
                    "distance": item.get("distance"),
                    "confidence": item.get("confidence"),
                }
            )
            continue

        attendance_result = attendance_service.mark_face_attendance(
            db,
            student_code=item["student_code"],
            confidence=item.get("confidence"),
        )
        attendance_results.append(attendance_result)

    return {
        "ok": True,
        "message": recognition_result.get("message", "Frame analyzed."),
        "recognition": recognition_result,
        "attendance_results": attendance_results,
    }
