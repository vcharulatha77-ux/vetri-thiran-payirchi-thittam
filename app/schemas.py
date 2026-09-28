from typing import Literal

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    character_name: str = Field(default="The Hero", min_length=1, max_length=60)
    setting: str = Field(default="A place full of wonder", min_length=1, max_length=100)
    tone: Literal["funny", "dramatic", "whimsical", "adventurous", "poetic"] = "adventurous"
    art_style: Literal["comic book", "anime", "watercolor", "pixel art", "storybook", "animated realistic"] = "storybook"
    generate_images: bool = True


class Panel(BaseModel):
    number: int
    title: str
    scene_description: str
    image_prompt: str
    narration: str
    dialogue: str = ""
    image_url: str = ""


class ComicResponse(BaseModel):
    comic_id: str
    title: str
    panels: list[Panel]
    pdf_url: str
    demo_mode: bool
