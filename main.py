import os
import sys
from pathlib import Path

from config import TimingConfig, VideoConfig, FontConfig, TTSConfig, get_theme
from data_loader import load_expressions
from tts_generator import generate_all_tts
from frame_renderer import render_expression_frame
from segment_builder import build_segment
from video_assembler import create_concat_list, concatenate_segments

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"


def main(data_path: str = None):
    if data_path is None:
        data_path = str(BASE_DIR / "data" / "expressions.csv")

    timing = TimingConfig()
    video = VideoConfig()
    fonts = FontConfig()
    tts = TTSConfig()

    for subdir in ["tts", "frames", "segments"]:
        (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # Step 1: Load data
    print("[1/5] Loading expressions...")
    expressions = load_expressions(data_path)
    total = len(expressions)
    print(f"      Loaded {total} expressions.")

    # Step 2: Generate TTS
    print("[2/5] Generating TTS audio...")
    tts_paths = generate_all_tts(expressions, str(OUTPUT_DIR / "tts"), tts)

    # Step 3: Render frames
    print("[3/5] Rendering frames...")
    frame_paths = {}
    for expr in expressions:
        theme = get_theme(expr.index)
        counter_text = f"{expr.index + 1} / {total}"
        progress = (expr.index + 1) / total
        frame_path = str(OUTPUT_DIR / "frames" / f"frame_{expr.index:03d}.png")
        render_expression_frame(
            expr.korean_text, expr.romanization, expr.english_text,
            counter_text, progress, theme, video, fonts, frame_path,
        )
        frame_paths[expr.index] = frame_path
    print(f"      Rendered {total} frames.")

    # Step 4: Build segments
    print("[4/5] Building video segments...")
    segment_paths = []
    for expr in expressions:
        seg_path = str(OUTPUT_DIR / "segments" / f"seg_{expr.index:03d}.mp4")
        if not os.path.exists(seg_path):
            build_segment(
                expr.index,
                frame_paths[expr.index],
                tts_paths[(expr.index, "en")],
                tts_paths[(expr.index, "kr")],
                seg_path,
                timing, video,
            )
        segment_paths.append(seg_path)
        print(f"      Segment {expr.index + 1}/{total} done.")

    # Step 5: Concatenate
    print("[5/5] Concatenating final video...")
    concat_list = str(OUTPUT_DIR / "concat_list.txt")
    create_concat_list(segment_paths, concat_list)
    final_path = str(OUTPUT_DIR / "final.mp4")
    concatenate_segments(concat_list, final_path)
    print(f"      Done! Output: {final_path}")


if __name__ == "__main__":
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(data_file)
