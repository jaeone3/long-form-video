import os
import asyncio
from pathlib import Path

import edge_tts

from config import TTSConfig
from data_loader import Expression

EDGE_VOICE_EN = "en-US-AriaNeural"
EDGE_VOICE_KR = "ko-KR-SunHiNeural"


async def _generate_tts_async(text: str, output_path: str, voice: str) -> str:
    if os.path.exists(output_path):
        return output_path
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def generate_tts(text: str, output_path: str, voice: str) -> str:
    return asyncio.run(_generate_tts_async(text, output_path, voice))


def generate_all_tts(
    expressions: list[Expression],
    output_dir: str,
    tts_config: TTSConfig,
) -> dict[tuple[int, str], str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paths = {}

    for expr in expressions:
        en_path = os.path.join(output_dir, f"en_{expr.index:03d}.mp3")
        kr_path = os.path.join(output_dir, f"kr_{expr.index:03d}.mp3")

        generate_tts(expr.english_text, en_path, EDGE_VOICE_EN)
        paths[(expr.index, "en")] = en_path

        generate_tts(expr.korean_text, kr_path, EDGE_VOICE_KR)
        paths[(expr.index, "kr")] = kr_path

        print(f"  TTS {expr.index + 1}/{len(expressions)}: {expr.english_text}")

    return paths
