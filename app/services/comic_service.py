import logging
import re
import uuid

from app.config import get_settings
from app.schemas import PromptRequest
from app.services.gemini_service import generate_outline, generate_story
from app.services.image_service import generate_image
from app.services.layout_builder import build_comic_layout
from app.services.pdf_service import save_pdf

logger = logging.getLogger(__name__)


def _demo_outline(request: PromptRequest) -> list[dict]:
    idea = request.prompt.rstrip(".!?")
    return [
        {"number": 1, "title": "A curious beginning", "scene_description": f"{request.character_name} sets out to explore {request.setting} after hearing a mysterious sound.", "image_prompt": f"{request.character_name} beginning an adventure in {request.setting}"},
        {"number": 2, "title": "A clue in the wild", "scene_description": f"A trail of glowing clues leads {request.character_name} deeper into the unknown.", "image_prompt": f"glowing clues in {request.setting}, curious hero follows"},
        {"number": 3, "title": "The unexpected obstacle", "scene_description": f"A surprising obstacle blocks the path, but a clever idea begins to take shape.", "image_prompt": f"unexpected friendly obstacle, expressive hero, {request.setting}"},
        {"number": 4, "title": "A brave new plan", "scene_description": f"With courage and kindness, {request.character_name} turns the problem into an opportunity.", "image_prompt": f"hero makes a clever brave plan in {request.setting}"},
        {"number": 5, "title": "A story to remember", "scene_description": f"The adventure ends with a joyful discovery: {idea}.", "image_prompt": f"joyful ending and discovery, {request.character_name}, {request.setting}"},
    ]


def _demo_story(request: PromptRequest, outline: list[dict]) -> list[dict]:
    lines = ["Every great adventure begins with one small step.", "The strange clues seemed to tell a story of their own.", "For a moment, the way forward looked impossible.", "Then a kind and clever idea changed everything.", "By sunset, the discovery belonged to everyone."]
    return [{"number": i + 1, "narration": f"{line} {panel['scene_description']}", "dialogue": ["‘Here I go!’", "‘That has to mean something.’", "‘We can solve this together.’", "‘I know just what to do!’", "‘What a wonderful day!’"][i]} for i, (line, panel) in enumerate(zip(lines, outline))]


async def create_comic(request: PromptRequest) -> dict:
    settings = get_settings()
    demo_mode = not bool(settings.gemini_api_key)
    try:
        if demo_mode:
            outline = _demo_outline(request)
            stories = _demo_story(request, outline)
        else:
            outline = generate_outline(request)
            stories = generate_story(request, outline)
    except Exception:
        logger.exception("AI story generation failed; using the local demo story.")
        outline = _demo_outline(request)
        stories = _demo_story(request, outline)
        demo_mode = True

    image_urls = []
    local_image_fallback = False
    image_errors = []
    if request.generate_images:
        for panel in outline:
            try:
                image_context = (
                    f"Story idea: {request.prompt}. Main character: {request.character_name}. "
                    f"Setting: {request.setting}. Tone: {request.tone}."
                )
                image_urls.append(await generate_image(panel.get("image_prompt", "comic panel"), request.art_style, image_context))
            except Exception as exc:
                logger.exception("Image generation failed; using local illustration.")
                local_image_fallback = True
                settings = get_settings()
                detail = str(exc) or "Image request failed."
                if settings.hf_api_key:
                    detail = detail.replace(settings.hf_api_key, "[token hidden]")
                    image_errors.append(f"{type(exc).__name__}: {detail[:220]}")
                else:
                    image_errors.append("No Hugging Face token is configured, so a local demo drawing was used.")
                # Retry without the remote image service using a local storybook illustration.
                from app.services.image_service import PANELS_DIR, create_local_illustration
                from uuid import uuid4
                PANELS_DIR.mkdir(parents=True, exist_ok=True)
                name = uuid4().hex + ".png"
                create_local_illustration(
                    f"Story idea: {request.prompt}. Main character: {request.character_name}. "
                    f"Setting: {request.setting}. Panel: {panel.get('image_prompt', 'comic panel')}",
                    request.art_style,
                    PANELS_DIR / name,
                )
                image_urls.append(f"/static/panels/{name}")
        if local_image_fallback:
            demo_mode = True
    else:
        image_urls = [""] * 5

    panels = build_comic_layout(outline, stories, image_urls)
    title = " ".join((request.prompt.split()[:7]))
    title = re.sub(r"[^\w ,!?'-]", "", title).strip().title() or f"{request.character_name}'s Adventure"
    pdf_filename = save_pdf(title, panels)
    image_message = "" if not image_errors else "Image service note: " + image_errors[0]
    return {"comic_id": uuid.uuid4().hex[:12], "title": title, "panels": panels, "pdf_filename": pdf_filename, "demo_mode": demo_mode, "image_message": image_message}
