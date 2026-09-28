import re
import uuid
import hashlib
import asyncio
from pathlib import Path

from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw

from app.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
PANELS_DIR = ROOT / "static" / "panels"


def create_local_illustration(prompt: str, style: str, path: Path) -> None:
    """Draw a full-body, animated storybook fox for offline/demo illustrations."""
    # Render at 2x then downsample for clean, smooth edges.
    scale = 2
    seed = int(hashlib.sha1(prompt.encode("utf-8", "ignore")).hexdigest()[:8], 16)
    scene = " ".join(prompt.lower().split())
    subjects = ["fox", "man", "woman", "boy", "girl", "person", "human", "astronaut", "scientist", "farmer", "pirate", "knight", "king", "queen"]
    subject_hits = []
    for word in subjects:
        match = re.search(rf"\b{re.escape(word)}\b", scene)
        if match:
            subject_hits.append((match.start(), word))
    first_subject = min(subject_hits, default=(len(scene) + 1, ""))[1]
    is_human = first_subject != "fox"
    if "beginning" in scene:
        variant = 0
    elif "clue" in scene or "glowing" in scene:
        variant = 1
    elif "obstacle" in scene:
        variant = 2
    elif "plan" in scene or "solve" in scene:
        variant = 3
    elif "joyful" in scene or "ending" in scene or "discovery" in scene:
        variant = 4
    else:
        variant = seed % 5
    skies = [(157, 218, 237), (72, 133, 158), (191, 217, 229), (247, 185, 119), (120, 183, 170)]
    greens = [(89, 151, 96), (60, 133, 111), (108, 160, 104), (130, 151, 87), (82, 147, 97)]
    hills = [(122, 185, 157), (80, 155, 153), (146, 185, 147), (193, 158, 104), (92, 162, 132)]
    sky, green, hill = skies[variant], greens[variant], hills[variant]
    image = Image.new("RGB", (1200 * scale, 760 * scale), sky)
    d = ImageDraw.Draw(image)
    draw_character_shapes = True

    def shape(kind, coords, **kwargs):
        if not draw_character_shapes:
            return
        coords = tuple(round(v * scale) for v in coords)
        getattr(d, kind)(coords, **kwargs)

    orange = (226, 105, 49)
    cream = (255, 226, 183)
    outline = (76, 48, 43)
    # Sunny sky, rolling meadow, distant hills, and simple storybook trees.
    shape("ellipse", (890, 55, 1030, 195), fill=(255, 222, 119) if variant != 1 else (251, 236, 173))
    shape("polygon", (0, 410, 180, 275, 360, 420, 540, 300, 760, 425, 970, 290, 1200, 420, 1200, 760, 0, 760), fill=hill)
    shape("rectangle", (0, 475, 1200, 760), fill=green)
    # Trees frame the action while keeping the whole character clearly visible.
    for x, top, width in [(75, 190, 150), (1020, 205, 155), (865, 295, 90), (245, 315, 80)]:
        shape("rectangle", (x + width * .43, top + 100, x + width * .57, 560), fill=(107, 72, 52))
        shape("ellipse", (x, top, x + width, top + 150), fill=(57, 123, 83))
        shape("ellipse", (x + 20, top - 30, x + width + 20, top + 105), fill=(72, 145, 92))
    # Low shadow anchors the fox's paws to the ground.
    shape("ellipse", (365, 641, 830, 690), fill=(61, 112, 72))

    # Give each beat a different landmark so the five panels read as story moments.
    if variant == 1:
        # A trail of magical clues leads toward a glowing star.
        for x, y, radius in [(340, 560, 12), (410, 525, 9), (865, 525, 11), (925, 490, 8)]:
            shape("ellipse", (x-radius, y-radius, x+radius, y+radius), fill=(255, 235, 135))
        shape("polygon", (920, 300, 934, 335, 972, 338, 943, 360, 952, 397, 920, 376, 889, 397, 898, 360, 869, 338, 906, 335), fill=(255, 236, 153))
    elif variant == 2:
        # A stream and stepping stones make the obstacle panel distinct.
        shape("polygon", (0, 575, 210, 540, 390, 582, 560, 535, 730, 590, 930, 540, 1200, 575, 1200, 760, 0, 760), fill=(69, 164, 192))
        for x, y in [(170, 635), (900, 610), (1010, 650)]:
            shape("ellipse", (x, y, x+125, y+35), fill=(205, 194, 152))
        shape("rounded_rectangle", (790, 430, 1060, 500), radius=25, fill=(111, 74, 49))
    elif variant == 3:
        # A small bridge and lantern suggest the fox's clever plan.
        shape("rectangle", (850, 455, 1130, 480), fill=(120, 75, 47))
        for x in [875, 965, 1055, 1110]:
            shape("line", (x, 455, x, 520), fill=(91, 59, 42), width=7 * scale)
        shape("ellipse", (270, 390, 330, 450), fill=(255, 225, 125))
    elif variant == 4:
        # A little treehouse and festive lights mark the happy ending.
        shape("rectangle", (875, 260, 1080, 400), fill=(147, 93, 59))
        shape("polygon", (845, 285, 978, 190, 1110, 285), fill=(112, 67, 50))
        shape("rectangle", (955, 325, 1000, 400), fill=(80, 53, 43))
        for x, y in [(830, 430), (1110, 440), (930, 465), (1060, 485)]:
            shape("ellipse", (x-10, y-10, x+10, y+10), fill=(255, 225, 125))

    draw_character_shapes = not is_human

    # Fox art is only used when the story actually names a fox.
    # Tail: large, fluffy, and unmistakably fox-like.
    shape("ellipse", (350, 435, 535, 590), fill=outline)
    shape("ellipse", (360, 444, 525, 580), fill=orange)
    shape("ellipse", (350, 485, 425, 585), fill=(255, 248, 228))
    # Four visible legs and paws; the fox is standing in a playful walking pose.
    shape("polygon", (505, 525, 570, 535, 550, 640, 490, 642), fill=outline)
    shape("polygon", (510, 532, 562, 540, 539, 630, 500, 632), fill=orange)
    shape("polygon", (655, 535, 718, 520, 741, 625, 687, 640), fill=outline)
    shape("polygon", (662, 540, 710, 530, 728, 615, 695, 625), fill=orange)
    shape("ellipse", (478, 625, 550, 651), fill=outline)
    shape("ellipse", (680, 622, 755, 650), fill=outline)
    # Body and cream bib.
    shape("ellipse", (455, 410, 748, 585), fill=outline)
    shape("ellipse", (465, 420, 738, 575), fill=orange)
    shape("ellipse", (540, 435, 685, 568), fill=cream)
    # Head with pointed ears, cream cheeks, muzzle, and a friendly expression.
    shape("polygon", (535, 385, 542, 265, 610, 325, 685, 260, 710, 390), fill=outline)
    shape("polygon", (548, 377, 552, 282, 608, 333, 680, 278, 698, 379), fill=orange)
    shape("polygon", (560, 350, 562, 300, 594, 333), fill=(248, 173, 154))
    shape("polygon", (652, 331, 676, 298, 680, 354), fill=(248, 173, 154))
    shape("ellipse", (535, 320, 710, 465), fill=outline)
    shape("ellipse", (544, 328, 702, 455), fill=orange)
    shape("ellipse", (558, 389, 688, 465), fill=cream)
    shape("ellipse", (585, 371, 598, 389), fill=outline)
    shape("ellipse", (650, 371, 663, 389), fill=outline)
    shape("ellipse", (619, 406, 638, 420), fill=outline)
    shape("arc", (600, 406, 654, 448), start=5, end=175, fill=outline, width=4 * scale)

    # Add a different action for each story beat instead of repeating one pose.
    if variant == 1:
        shape("line", (680, 465, 760, 400, 810, 360), fill=outline, width=24 * scale)
        shape("line", (680, 465, 760, 400, 810, 360), fill=orange, width=15 * scale)
        shape("ellipse", (795, 345, 830, 375), fill=cream, outline=outline, width=4 * scale)
    elif variant == 2:
        shape("line", (680, 475, 770, 490, 800, 470), fill=outline, width=24 * scale)
        shape("line", (680, 475, 770, 490, 800, 470), fill=orange, width=15 * scale)
        shape("ellipse", (785, 458, 820, 488), fill=cream, outline=outline, width=4 * scale)
    elif variant == 3:
        shape("line", (520, 470, 450, 425, 425, 380), fill=outline, width=24 * scale)
        shape("line", (520, 470, 450, 425, 425, 380), fill=orange, width=15 * scale)
        shape("ellipse", (408, 360, 442, 394), fill=cream, outline=outline, width=4 * scale)
    elif variant == 4:
        shape("rounded_rectangle", (755, 500, 835, 565), radius=8, fill=(255, 246, 218), outline=outline, width=4 * scale)
        shape("line", (795, 510, 795, 552), fill=(148, 94, 61), width=3 * scale)
        for x, y in [(490, 350), (755, 365), (820, 420), (425, 390)]:
            shape("line", (x-9, y, x+9, y), fill=(255, 224, 115), width=3 * scale)
            shape("line", (x, y-9, x, y+9), fill=(255, 224, 115), width=3 * scale)

    if is_human:
        draw_character_shapes = True
        skin = (232, 177, 135)
        clothes = [(66, 113, 172), (163, 82, 63), (79, 132, 91), (113, 91, 154), (182, 119, 57)][variant]
        dark = (52, 47, 52)
        # Full-body person with visible head, torso, arms, legs and boots.
        shape("polygon", (520, 520, 584, 520, 575, 632, 520, 632), fill=dark)
        shape("polygon", (635, 520, 700, 520, 711, 632, 654, 632), fill=dark)
        shape("ellipse", (502, 620, 585, 654), fill=(55, 47, 47))
        shape("ellipse", (650, 620, 735, 654), fill=(55, 47, 47))
        shape("polygon", (498, 410, 700, 410, 720, 548, 490, 548), fill=dark)
        shape("polygon", (508, 420, 690, 420, 705, 535, 500, 535), fill=clothes)
        shape("polygon", (500, 432, 530, 438, 505, 540, 470, 530), fill=dark)
        shape("polygon", (505, 440, 525, 444, 500, 527, 480, 520), fill=skin)
        shape("polygon", (672, 435, 705, 430, 744, 510, 715, 525), fill=dark)
        shape("polygon", (680, 443, 697, 440, 729, 506, 711, 512), fill=skin)
        shape("rectangle", (584, 385, 628, 434), fill=skin)
        shape("ellipse", (530, 270, 682, 420), fill=dark)
        shape("ellipse", (539, 282, 673, 412), fill=skin)
        shape("ellipse", (564, 335, 576, 351), fill=dark)
        shape("ellipse", (628, 335, 640, 351), fill=dark)
        shape("arc", (580, 344, 630, 385), start=10, end=170, fill=dark, width=4 * scale)
        shape("polygon", (535, 321, 545, 282, 585, 305, 635, 280, 675, 315, 667, 292, 625, 260, 564, 265), fill=(76, 52, 43))
        # A distinct gesture on each panel to keep the person from becoming a repeated pose.
        if variant == 1:
            shape("line", (692, 450, 757, 390, 795, 337), fill=dark, width=22 * scale)
            shape("line", (692, 450, 757, 390, 795, 337), fill=skin, width=13 * scale)
            shape("ellipse", (782, 322, 812, 352), fill=(255, 226, 135))
        elif variant == 2:
            shape("line", (510, 455, 450, 490, 410, 480), fill=dark, width=22 * scale)
            shape("line", (510, 455, 450, 490, 410, 480), fill=skin, width=13 * scale)
        elif variant == 3:
            shape("line", (690, 455, 770, 470, 810, 445), fill=dark, width=22 * scale)
            shape("line", (690, 455, 770, 470, 810, 445), fill=skin, width=13 * scale)
        elif variant == 4:
            shape("line", (520, 450, 470, 380, 460, 335), fill=dark, width=22 * scale)
            shape("line", (520, 450, 470, 380, 460, 335), fill=skin, width=13 * scale)
            shape("line", (685, 450, 745, 380, 755, 335), fill=dark, width=22 * scale)
            shape("line", (685, 450, 745, 380, 755, 335), fill=skin, width=13 * scale)

    # A few bright flowers add animated storybook detail without covering the fox.
    for x, y in [(285, 615), (900, 620), (820, 520), (420, 570)]:
        shape("line", (x, y, x, y + 35), fill=(50, 105, 62), width=3 * scale)
        shape("ellipse", (x - 9, y - 10, x + 9, y + 8), fill=(255, 245, 218))
        shape("ellipse", (x - 4, y - 5, x + 4, y + 3), fill=(250, 195, 75))

    image = image.resize((1200, 760), Image.Resampling.LANCZOS)
    image.save(path, format="PNG")


async def generate_image(prompt: str, style: str = "comic book", context: str = "") -> str:
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    name = uuid.uuid4().hex
    path = PANELS_DIR / f"{name}.png"
    if settings.hf_api_key:
        if style == "animated realistic":
            style_direction = (
                "high-quality animated feature film still, natural realistic fox anatomy and fur, "
                "soft painterly light, richly detailed forest, believable colors, cinematic storybook illustration"
            )
        else:
            style_direction = f"polished {style} illustration"
        image_prompt = (
            f"{style_direction}. Illustrate the main character and action exactly as described "
            f"in the story. Preserve the specified person, animal, creature, or object; do not "
            f"substitute a fox or add an unrequested character. Wide landscape story frame with "
            f"the subject fully visible in its natural setting, expressive pose, consistent design, "
            f"and no text or lettering. Story context: {context}. Panel scene: {prompt}"
        )
        def request_image():
            client = InferenceClient(
                provider="auto",
                api_key=settings.hf_api_key,
                timeout=settings.image_timeout_seconds,
            )
            return client.text_to_image(image_prompt, model=settings.hf_image_model)

        generated = await asyncio.to_thread(request_image)
        generated.save(path, format="PNG")
        return f"/static/panels/{path.name}"
    create_local_illustration(f"{context}. {prompt}", style, path)
    return f"/static/panels/{path.name}"


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()[:60] or "comic"
