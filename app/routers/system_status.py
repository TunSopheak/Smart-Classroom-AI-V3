from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import system_status_service

router = APIRouter(tags=["system-status"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    status = system_status_service.get_system_status(db)
    return JSONResponse(content=jsonable_encoder(status))


@router.get("/system-status", response_class=HTMLResponse)
def system_status_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "status": system_status_service.get_system_status(db),
    }
    return templates.TemplateResponse(request, "system_status.html", context)
