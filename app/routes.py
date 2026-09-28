import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.schemas import ComicResponse, PromptRequest
from app.services.comic_service import create_comic
from app.services.image_service import generate_image

logger = logging.getLogger(__name__)
router = APIRouter()
ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"app_name": get_settings().app_name})


@router.post("/generate", response_class=HTMLResponse)
async def generate_form(request: Request, prompt: str = Form(...), character_name: str = Form("The Hero"), setting: str = Form("A place full of wonder"), tone: str = Form("adventurous"), art_style: str = Form("comic book"), generate_images: bool = Form(False)):
    try:
        payload = PromptRequest(prompt=prompt, character_name=character_name, setting=setting, tone=tone, art_style=art_style, generate_images=generate_images)
        comic = await create_comic(payload)
        return templates.TemplateResponse(request=request, name="comic_preview.html", context={**comic, "app_name": get_settings().app_name})
    except Exception as exc:
        logger.exception("Could not generate the comic.")
        detail = str(exc).strip() or repr(exc) or "No additional error details were provided."
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            status_code=400,
            context={"app_name": get_settings().app_name, "error": f"{type(exc).__name__}: {detail}"},
        )


@router.post("/generate-comic/json", response_model=ComicResponse)
async def generate_json(payload: PromptRequest):
    try:
        comic = await create_comic(payload)
        return ComicResponse(comic_id=comic["comic_id"], title=comic["title"], panels=comic["panels"], pdf_url=f"/download/{comic['pdf_filename']}", demo_mode=comic["demo_mode"])
    except Exception as exc:
        logger.exception("JSON comic generation failed.")
        raise HTTPException(status_code=500, detail="Comic generation failed. Check the server log and model configuration.") from exc


@router.get("/download/{filename}")
async def download_pdf(filename: str):
    if not filename.startswith("comic-") or not filename.endswith(".pdf") or Path(filename).name != filename:
        raise HTTPException(status_code=404, detail="PDF not found")
    path = ROOT / "static" / "exports" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename="comiccraft-comic.pdf", headers={"X-ComicCraft-Success": "/export-success"})


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request):
    return templates.TemplateResponse(request=request, name="export_success.html", context={"app_name": get_settings().app_name})


@router.post("/test-image")
async def test_image(prompt: str = Form(...)):
    try:
        image_url = await generate_image(prompt)
        return JSONResponse({"image_url": image_url})
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Image generation failed. Check the HF token and model configuration.") from exc
