from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import student_service, training_service

router = APIRouter(prefix="/training", tags=["training"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def training_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "students": student_service.get_students(db),
        "training_status": training_service.get_training_status(db),
    }
    return templates.TemplateResponse(request, "training.html", context)


@router.get("/status")
def training_status(db: Session = Depends(get_db)):
    return training_service.get_training_status(db)


@router.post("/capture")
def capture_face_image(
    student_code: str = Form(...),
    image_data: str = Form(...),
    db: Session = Depends(get_db),
):
    result = training_service.save_face_capture(db, student_code, image_data)
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status_code)


@router.post("/train")
def train_face_model():
    result = training_service.train_model()
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status_code)
