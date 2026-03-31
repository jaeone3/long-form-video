from dataclasses import dataclass, field


@dataclass
class TimingConfig:
    think_pause_sec: float = 0.5
    shadowing_pause_sec: float = 2.0
    transition_sec: float = 0.5


@dataclass
class VideoConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    audio_sample_rate: int = 44100
    crf: int = 23
    preset: str = "medium"


@dataclass
class FontConfig:
    korean_font: str = "/Users/jeongseojin/Library/Fonts/NanumSquareRoundOTFEB.otf"
    korean_size: int = 130
    romanization_font: str = "/Users/jeongseojin/Library/Fonts/NanumSquareRoundOTFR.otf"
    romanization_size: int = 36
    english_font: str = "/System/Library/Fonts/Avenir Next.ttc"
    english_size: int = 50
    counter_font: str = "/System/Library/Fonts/Avenir Next.ttc"
    counter_size: int = 24


@dataclass
class ColorTheme:
    background: str
    korean_text: str
    romanization_text: str
    english_text: str
    progress_bar: str
    progress_bg: str


@dataclass
class TTSConfig:
    model: str = "gpt-4o-mini-tts"
    english_voice: str = "coral"
    korean_voice: str = "coral"
    korean_instructions: str = "Speak in Korean clearly and at a natural pace suitable for language learners."
    english_instructions: str = "Speak in English clearly and at a natural pace."
    response_format: str = "mp3"
    speed: float = 1.0


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL (0-360, 0-1, 0-1) to RGB (0-255)."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def get_theme_for_day(day: int, round_num: int = 1) -> ColorTheme:
    """Generate a unique bright gradient theme for each day (1-365).
    Each round shifts the hue so rotations get fresh colors."""

    # Shift hue by ~137.5° (golden angle) per round for maximum color distance
    round_offset = (round_num - 1) * 137.508
    hue = ((day * 360.0 / 365.0) + round_offset) % 360.0

    # Use both hue and slight lightness/saturation variation to guarantee uniqueness
    lightness = 0.90 + 0.04 * ((day * 7) % 17) / 16.0  # 0.90 ~ 0.94
    sat = 0.65 + 0.15 * ((day * 11) % 13) / 12.0  # 0.65 ~ 0.80

    bg = _hsl_to_rgb(hue, sat, lightness)
    bg_hex = _rgb_to_hex(*bg)

    # Edge color for gradient (darker, same hue)
    edge = _hsl_to_rgb(hue, sat - 0.10, lightness - 0.08)
    edge_hex = _rgb_to_hex(*edge)

    # Progress bar: saturated version of the hue
    bar = _hsl_to_rgb(hue, 0.70, 0.45)
    bar_hex = _rgb_to_hex(*bar)

    return ColorTheme(
        background=bg_hex,
        korean_text="#222222",
        romanization_text="#888888",
        english_text="#222222",
        progress_bar=bar_hex,
        progress_bg=edge_hex,
    )


def get_theme(index: int, video_seed: int = 0, round_num: int = 1) -> ColorTheme:
    """Each video (day) gets one unique theme. All expressions in
    that video share the same background."""
    return get_theme_for_day(video_seed % 365, round_num)
