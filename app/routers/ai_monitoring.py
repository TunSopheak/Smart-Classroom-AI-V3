from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.ai import face_training
from app.core.database import get_db
from app.services import attendance_service, behavior_service, face_attendance_service

router = APIRouter(prefix="/ai-monitoring", tags=["ai-monitoring"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def ai_monitoring_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": attendance_service.attendance_summary(db),
        "recent": attendance_service.recent_attendance(db, limit=10),
        "behavior": behavior_service.placeholder_behavior_summary(),
        "face_model": face_training.model_status(),
    }
    return templates.TemplateResponse(request, "ai_monitoring.html", context)


@router.post("/analyze-frame")
def analyze_frame_for_face_attendance(
    image_data: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        face_result = face_attendance_service.analyze_frame_for_attendance(db, image_data)
        behavior_result = behavior_service.analyze_behavior_frame(image_data)

        result = {
            "ok": True,
            "message": "Frame analyzed successfully.",
            "face_attendance": face_result,
            "recognition": face_result.get("recognition", {}),
            "attendance_results": face_result.get("attendance_results", []),
            "behavior": behavior_result,
        }

        if not face_result.get("ok"):
            result["ok"] = False
            result["message"] = face_result.get("message", "Face attendance analysis failed.")

        return JSONResponse(content=jsonable_encoder(result), status_code=200)

    except Exception as exc:
        return JSONResponse(
            content=jsonable_encoder(
                {
                    "ok": False,
                    "message": f"Analyze frame failed: {type(exc).__name__}: {exc}",
                    "recognition": {
                        "recognitions": [],
                        "face_count": 0,
                        "recognized_count": 0,
                    },
                    "attendance_results": [],
                    "behavior": behavior_service.placeholder_behavior_summary(),
                }
            ),
            status_code=500,
        )
