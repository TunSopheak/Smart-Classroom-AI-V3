from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def sessions_page(request: Request, db: Session = Depends(get_db)):
    context = {
        "request": request,
        "sessions": session_service.get_sessions(db),
    }
    return templates.TemplateResponse(request, "sessions.html", context)


@router.post("/{session_id}/start")
def start_session(session_id: int, db: Session = Depends(get_db)):
    session_service.start_session(db, session_id)
    return RedirectResponse("/sessions", status_code=303)


@router.post("/{session_id}/close")
def close_session(session_id: int, db: Session = Depends(get_db)):
    session_service.close_session(db, session_id)
    return RedirectResponse("/sessions", status_code=303)
