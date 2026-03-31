import os
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import VideoConfig, FontConfig, ColorTheme

FLAG_PATH = os.path.join(os.path.dirname(__file__), "assets", "flag.png")
_flag_cache = {}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _vary_color(hex_color: str, amount: int = 3) -> tuple[int, int, int]:
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, min(255, r + random.randint(-amount, amount)))
    g = max(0, min(255, g + random.randint(-amount, amount)))
    b = max(0, min(255, b + random.randint(-amount, amount)))
    return (r, g, b)


def _draw_centered_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont,
                         fill, y: int, width: int):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _fit_text(draw: ImageDraw.Draw, text: str, font_path: str, max_size: int,
              max_width: int) -> ImageFont.FreeTypeFont:
    size = max_size
    font = ImageFont.truetype(font_path, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    while bbox[2] - bbox[0] > max_width and size > 20:
        size -= 2
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
    return font


def _get_flag_rect(size: int) -> Image.Image:
    """Load flag as rectangle with white background, as in reference."""
    key = ("rect", size)
    if key not in _flag_cache:
        flag = Image.open(FLAG_PATH).convert("RGBA")
        ratio = size / flag.width
        new_h = int(flag.height * ratio)
        flag = flag.resize((size, new_h), Image.LANCZOS)
        _flag_cache[key] = flag
    return _flag_cache[key]


def _draw_radial_gradient_smooth(w: int, h: int, center_color: tuple, edge_color: tuple) -> Image.Image:
    """Smooth radial gradient — center bright, edges darker. (numpy vectorized)"""
    cx, cy = w // 2, h // 2
    max_dist = math.sqrt(cx * cx + cy * cy)

    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    frac = np.clip(dist / max_dist, 0.0, 1.0)

    # Ease — only affect outer 40%
    blend = np.where(frac > 0.6, ((frac - 0.6) / 0.4) ** 2, 0.0)

    center = np.array(center_color, dtype=np.float32)
    edge = np.array(edge_color, dtype=np.float32)
    diff = edge - center

    arr = np.full((h, w, 3), center, dtype=np.float32)
    arr += blend[..., np.newaxis] * diff
    arr = np.clip(arr, 0, 255).astype(np.uint8)

    return Image.fromarray(arr, "RGB")


KOREAN_FONTS_BOLD = [
    "/Users/jeongseojin/Library/Fonts/NanumSquareRoundOTFEB.otf",
    "/Users/jeongseojin/Library/Fonts/NanumSquareRoundOTFB.otf",
]

KOREAN_FONTS_REGULAR = [
    "/Users/jeongseojin/Library/Fonts/NanumSquareRoundOTFR.otf",
]


def _pick_font(fonts: list[str], seed: int) -> str:
    rng = random.Random(seed)
    return rng.choice(fonts)


def _add_subtle_noise(img: Image.Image, intensity: int = 2) -> Image.Image:
    arr = np.array(img)
    noise = np.random.randint(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def render_expression_frame(
    korean_text: str,
    romanization: str,
    english_text: str,
    counter_text: str,
    progress_fraction: float,
    theme: ColorTheme,
    video: VideoConfig,
    fonts: FontConfig,
    output_path: str,
) -> str:
    seed = hash(korean_text + english_text)
    rng = random.Random(seed)

    y_offset = rng.randint(-4, 4)
    flag_size_var = rng.randint(-3, 3)

    # Smooth radial gradient background
    center_bg = _vary_color(theme.background, amount=2)
    edge_bg = (
        max(0, center_bg[0] - 15),
        max(0, center_bg[1] - 15),
        max(0, center_bg[2] - 12),
    )
    img = _draw_radial_gradient_smooth(video.width, video.height, center_bg, edge_bg)
    draw = ImageDraw.Draw(img)

    max_text_width = video.width - 200
    center_x = video.width // 2

    kr_bold = _pick_font(KOREAN_FONTS_BOLD, seed)
    kr_regular = KOREAN_FONTS_REGULAR[0]

    # === LAYOUT — matching reference tightly ===

    # --- Flag (circular, white bg) ---
    flag_size = 210 + flag_size_var
    flag_img = _get_flag_rect(flag_size)
    flag_x = center_x - flag_img.width // 2
    flag_y = int(video.height * 0.12) + y_offset
    img.paste(flag_img, (flag_x, flag_y), flag_img)
    draw = ImageDraw.Draw(img)

    # --- English (regular weight, not bold, dark gray #333) ---
    en_y = int(video.height * 0.32) + y_offset
    font_en = _fit_text(draw, english_text, fonts.english_font, fonts.english_size, max_text_width)
    _draw_centered_text(draw, english_text, font_en,
                        _hex_to_rgb(theme.english_text), en_y, video.width)

    # --- Korean (bold, large, very close below English) ---
    kr_y = int(video.height * 0.39) + y_offset
    font_kr = _fit_text(draw, korean_text, kr_bold, fonts.korean_size, max_text_width)
    _draw_centered_text(draw, korean_text, font_kr,
                        _hex_to_rgb(theme.korean_text), kr_y, video.width)

    # --- Romanization (regular, gray, tight below Korean) ---
    rom_display = f"[{romanization}]"
    rom_y = int(video.height * 0.53) + y_offset
    font_rom = _fit_text(draw, rom_display, kr_regular, fonts.romanization_size, max_text_width)
    _draw_centered_text(draw, rom_display, font_rom,
                        _hex_to_rgb(theme.romanization_text), rom_y, video.width)

    # No counter — matching reference

    # --- Koko AI logo at bottom with rounded corners ---
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "koko_logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_w = 500
        ratio = logo_w / logo.width
        logo_h = int(logo.height * ratio)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        # Round corners
        corner_radius = 20
        mask = Image.new("L", (logo_w, logo_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, logo_w, logo_h], radius=corner_radius, fill=255)
        logo.putalpha(mask)

        logo_x = center_x - logo_w // 2
        logo_y = int(video.height * 0.72)
        img.paste(logo, (logo_x, logo_y), logo)
        draw = ImageDraw.Draw(img)

    # --- Progress bar ---
    bar_y = video.height - 25
    bar_height = 4
    draw.rectangle([0, bar_y, video.width, bar_y + bar_height],
                   fill=_hex_to_rgb(theme.progress_bg))
    draw.rectangle([0, bar_y, int(video.width * progress_fraction), bar_y + bar_height],
                   fill=_hex_to_rgb(theme.progress_bar))

    # Noise
    img = _add_subtle_noise(img, intensity=2)

    img.save(output_path, "PNG")
    return output_path
