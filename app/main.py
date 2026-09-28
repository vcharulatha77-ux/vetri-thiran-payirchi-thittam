from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import router

ROOT = Path(__file__).resolve().parent.parent
for directory in (ROOT / "static" / "panels", ROOT / "static" / "exports"):
    directory.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=get_settings().app_name, version="1.0.0", description="Create illustrated five-panel comics from a story idea.")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
app.include_router(router)


@app.get("/health")
async def health():
    settings = get_settings()
    return {"status": "ok", "gemini_configured": bool(settings.gemini_api_key), "image_service_configured": bool(settings.hf_api_key)}
