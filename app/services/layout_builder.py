from app.schemas import Panel


def build_comic_layout(outline: list[dict], stories: list[dict], image_urls: list[str]) -> list[Panel]:
    stories_by_number = {int(item.get("number", i + 1)): item for i, item in enumerate(stories)}
    panels = []
    for i, item in enumerate(outline[:5]):
        number = i + 1
        story = stories_by_number.get(number, {})
        panels.append(Panel(
            number=number,
            title=str(item.get("title", f"Panel {number}"))[:100],
            scene_description=str(item.get("scene_description", ""))[:700],
            image_prompt=str(item.get("image_prompt", ""))[:700],
            narration=str(story.get("narration", item.get("scene_description", "")))[:1200],
            dialogue=str(story.get("dialogue", ""))[:600],
            image_url=image_urls[i] if i < len(image_urls) else "",
        ))
    return panels
