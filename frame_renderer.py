from PIL import Image, ImageDraw, ImageFont

from config import VideoConfig, FontConfig, ColorTheme


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


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
    bg = _hex_to_rgb(theme.background)
    img = Image.new("RGB", (video.width, video.height), bg)
    draw = ImageDraw.Draw(img)

    max_text_width = video.width - 200

    # Korean text - center, large bold
    font_kr = _fit_text(draw, korean_text, fonts.korean_font, fonts.korean_size, max_text_width)
    _draw_centered_text(draw, korean_text, font_kr, _hex_to_rgb(theme.korean_text), 380, video.width)

    # Romanization - below Korean
    font_rom = _fit_text(draw, romanization, fonts.romanization_font, fonts.romanization_size, max_text_width)
    _draw_centered_text(draw, romanization, font_rom, _hex_to_rgb(theme.romanization_text), 490, video.width)

    # English - below romanization
    font_en = _fit_text(draw, english_text, fonts.english_font, fonts.english_size, max_text_width)
    _draw_centered_text(draw, english_text, font_en, _hex_to_rgb(theme.english_text), 580, video.width)

    # Counter - top right
    font_ctr = ImageFont.truetype(fonts.counter_font, fonts.counter_size)
    ctr_bbox = draw.textbbox((0, 0), counter_text, font=font_ctr)
    ctr_w = ctr_bbox[2] - ctr_bbox[0]
    draw.text((video.width - ctr_w - 60, 40), counter_text, font=font_ctr,
              fill=_hex_to_rgb(theme.english_text))

    # Progress bar - bottom
    bar_y = video.height - 50
    bar_height = 8
    bar_margin = 60
    bar_full_width = video.width - 2 * bar_margin
    draw.rectangle(
        [bar_margin, bar_y, bar_margin + bar_full_width, bar_y + bar_height],
        fill=_hex_to_rgb(theme.progress_bg),
    )
    draw.rectangle(
        [bar_margin, bar_y, bar_margin + int(bar_full_width * progress_fraction), bar_y + bar_height],
        fill=_hex_to_rgb(theme.progress_bar),
    )

    img.save(output_path, "PNG")
    return output_path
