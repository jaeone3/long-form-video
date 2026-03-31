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
    korean_font: str = "C:/Windows/Fonts/malgunbd.ttf"
    korean_size: int = 80
    romanization_font: str = "C:/Windows/Fonts/malgun.ttf"
    romanization_size: int = 40
    english_font: str = "C:/Windows/Fonts/arial.ttf"
    english_size: int = 36
    counter_font: str = "C:/Windows/Fonts/arial.ttf"
    counter_size: int = 28


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


COLOR_THEMES = [
    ColorTheme("#1a1a2e", "#ffffff", "#a0a0c0", "#808090", "#4ecca3", "#333355"),
    ColorTheme("#16213e", "#ffffff", "#a0b0d0", "#7080a0", "#e94560", "#2a3a5e"),
    ColorTheme("#0f3460", "#ffffff", "#90b0e0", "#6090c0", "#e94560", "#1a4a70"),
    ColorTheme("#1b262c", "#ffffff", "#a0c0d0", "#7090a0", "#bbe1fa", "#2b3a42"),
    ColorTheme("#2d2d2d", "#ffffff", "#c0c0c0", "#909090", "#f0a500", "#444444"),
    ColorTheme("#1a1a2e", "#ffffff", "#c0a0c0", "#9080a0", "#e056a0", "#333355"),
    ColorTheme("#162e21", "#ffffff", "#a0d0b0", "#70a080", "#45e960", "#2a5e3a"),
    ColorTheme("#2e1a1a", "#ffffff", "#d0a0a0", "#a07070", "#e96045", "#553333"),
    ColorTheme("#1a2e2e", "#ffffff", "#a0c0d0", "#709090", "#45c5e9", "#2a4a55"),
    ColorTheme("#2e2e1a", "#ffffff", "#d0d0a0", "#a0a070", "#e9e045", "#555533"),
]


def get_theme(index: int) -> ColorTheme:
    return COLOR_THEMES[index // 10 % len(COLOR_THEMES)]
