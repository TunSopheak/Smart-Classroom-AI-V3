from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import video_record_service

router = APIRouter(prefix="/video-records", tags=["video-records"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def video_records_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "records": video_record_service.list_video_records(db),
        "summary": video_record_service.video_summary(db),
    }
    return templates.TemplateResponse(request, "video_records.html", context)


@router.post("/upload")
async def upload_video_record(
    video_file: UploadFile = File(...),
    event_type: str = Form("manual_clip"),
    note: str = Form(""),
    duration_seconds: float = Form(0),
    db: Session = Depends(get_db),
):
    try:
        content = await video_file.read()

        if not content:
            return JSONResponse(
                content={"ok": False, "message": "Empty video file."},
                status_code=400,
            )

        record = video_record_service.save_video_bytes_for_active_session(
            db=db,
            content=content,
            original_filename=video_file.filename or "ai_monitoring_clip.webm",
            mime_type=video_file.content_type or "video/webm",
            event_type=event_type,
            note=note,
            duration_seconds=duration_seconds,
        )

        return JSONResponse(
            content=jsonable_encoder(
                {
                    "ok": True,
                    "message": "Video evidence saved successfully.",
                    "record_id": record.id,
                    "video_path": record.video_path,
                    "title": record.title,
                }
            )
        )

    except Exception as exc:
        return JSONResponse(
            content={
                "ok": False,
                "message": f"Save video failed: {type(exc).__name__}: {exc}",
            },
            status_code=500,
        )
