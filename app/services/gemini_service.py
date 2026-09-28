import json

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas import PromptRequest


def _generate_json(prompt: str) -> dict | list:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000))
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.85),
    )
    text = response.text or ""
    return json.loads(text)


def generate_outline(request: PromptRequest) -> list[dict]:
    prompt = f"""Create exactly five sequential comic panels. Return JSON only as {{"title":"...","panels":[{{"number":1,"title":"...","scene_description":"...","image_prompt":"..."}}]}}.
Idea: {request.prompt}\nHero: {request.character_name}\nSetting: {request.setting}\nTone: {request.tone}\nArt style: {request.art_style}.
Make the story coherent with a clear beginning, complication, and satisfying ending. Image prompts must describe one readable comic illustration without lettering or speech bubbles."""
    result = _generate_json(prompt)
    panels = result.get("panels", []) if isinstance(result, dict) else result
    if not isinstance(panels, list) or len(panels) < 5:
        raise ValueError("Gemini did not return five usable panel outlines.")
    return panels[:5]


def generate_story(request: PromptRequest, outline: list[dict]) -> list[dict]:
    prompt = f"""Expand this five-panel outline into concise comic narration and one short spoken line per panel. Return JSON only as {{"panels":[{{"number":1,"narration":"...","dialogue":"..."}}]}}. Keep names and plot consistent. Tone: {request.tone}. Hero: {request.character_name}. Outline: {json.dumps(outline, ensure_ascii=False)}"""
    result = _generate_json(prompt)
    panels = result.get("panels", []) if isinstance(result, dict) else result
    if not isinstance(panels, list) or len(panels) < 5:
        raise ValueError("Gemini did not return five usable story panels.")
    return panels[:5]
