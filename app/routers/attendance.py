import base64

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def attendance_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "summary": attendance_service.attendance_summary(db),
        "records": attendance_service.recent_attendance(db, limit=50),
    }
    return templates.TemplateResponse(request, "attendance.html", context)


@router.post("/demo-face")
def demo_face_attendance(
    student_code: str = Form(...),
    confidence: float = Form(85.0),
    db: Session = Depends(get_db),
):
    attendance_service.mark_face_attendance(db, student_code=student_code, confidence=confidence)
    return RedirectResponse("/attendance", status_code=303)


@router.get("/qr-scan", response_class=HTMLResponse)
def student_qr_scan_page(
    request: Request,
    student_code: str,
    token: str,
    db: Session = Depends(get_db),
):
    result = attendance_service.mark_qr_attendance(
        db,
        student_code=student_code,
        token=token,
    )

    context = {
        "request": request,
        "result": result,
        "student_code": student_code,
    }

    return templates.TemplateResponse(request, "student_qr_scan_result.html", context)


@router.get("/qr-scanner", response_class=HTMLResponse)
def qr_scanner_page(request: Request):
    return templates.TemplateResponse(request, "qr_scanner.html", {"request": request})


@router.post("/qr-decode-frame")
def qr_decode_frame(image_data: str = Form(...)):
    try:
        import cv2
        import numpy as np

        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        raw = base64.b64decode(image_data)
        image_array = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if frame is None:
            return {"ok": False, "reason": "invalid_frame"}

        detector = cv2.QRCodeDetector()
        value, points, _ = detector.detectAndDecode(frame)

        if not value:
            return {"ok": False, "reason": "no_qr_detected"}

        return {
            "ok": True,
            "value": value,
        }

    except Exception as exc:
        return {
            "ok": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }


@router.get("/qr-scan-api")
def student_qr_scan_api(
    student_code: str,
    token: str,
    db: Session = Depends(get_db),
):
    return attendance_service.mark_qr_attendance(
        db,
        student_code=student_code,
        token=token,
    )
