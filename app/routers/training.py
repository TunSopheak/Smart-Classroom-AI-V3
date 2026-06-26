from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/training", tags=["training"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def training_page(request: Request):
    context = {"request": request}
    return templates.TemplateResponse(request, "training.html", context)
