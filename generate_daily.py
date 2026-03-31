"""Generate videos for a given day range.

Usage:
    python3 generate_daily.py <start_day> [end_day]

Examples:
    python3 generate_daily.py 1        # Generate Day 1 only
    python3 generate_daily.py 1 7      # Generate Day 1-7
    python3 generate_daily.py 1 7 -n 3 # Generate 3 videos from Day 1-7
"""
import os
import sys
import csv
import shutil
from datetime import date
from pathlib import Path

from config import TimingConfig, VideoConfig, FontConfig, TTSConfig, get_theme_for_day
from data_loader import load_expressions
from tts_generator import generate_all_tts
from frame_renderer import render_expression_frame, _flag_cache
from segment_builder import build_segment
from video_assembler import create_concat_list, concatenate_segments

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def generate_video_for_day(day: int):
    """Generate one complete video for a given day number (1-365)."""

    # Check if CSV exists for this day
    csv_path = DATA_DIR / f"day{day:03d}.csv"
    if not csv_path.exists():
        print(f"  ⚠ CSV not found: {csv_path} — skipping Day {day}")
        return None

    # Create day-specific output folder
    day_dir = OUTPUT_DIR / f"day{day:03d}"
    for subdir in ["tts", "frames", "segments"]:
        (day_dir / subdir).mkdir(parents=True, exist_ok=True)

    timing = TimingConfig()
    video = VideoConfig()
    fonts = FontConfig()
    tts = TTSConfig()

    # Clear flag cache for fresh rendering
    _flag_cache.clear()

    # Get unique theme for this day
    theme = get_theme_for_day(day)

    print(f"\n{'='*50}")
    print(f"  Day {day} — {theme.background}")
    print(f"{'='*50}")

    # Step 1: Load data
    expressions = load_expressions(str(csv_path))
    total = len(expressions)
    print(f"  [1/5] Loaded {total} expressions")

    # Step 2: TTS
    print(f"  [2/5] Generating TTS...")
    tts_paths = generate_all_tts(expressions, str(day_dir / "tts"), tts)

    # Step 3: Render frames
    print(f"  [3/5] Rendering frames...")
    frame_paths = {}
    for expr in expressions:
        counter_text = ""
        progress = (expr.index + 1) / total
        frame_path = str(day_dir / "frames" / f"frame_{expr.index:03d}.png")
        render_expression_frame(
            expr.korean_text, expr.romanization, expr.english_text,
            counter_text, progress, theme, video, fonts, frame_path,
        )
        frame_paths[expr.index] = frame_path
    print(f"  [3/5] Rendered {total} frames")

    # Step 4: Build segments
    print(f"  [4/5] Building segments...")
    segment_paths = []
    for expr in expressions:
        seg_path = str(day_dir / "segments" / f"seg_{expr.index:03d}.mp4")
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
    print(f"  [4/5] Built {total} segments")

    # Step 5: Concatenate
    print(f"  [5/5] Concatenating...")
    concat_list = str(day_dir / "concat_list.txt")
    create_concat_list(segment_paths, concat_list)
    final_path = str(day_dir / f"day{day:03d}_final.mp4")
    concatenate_segments(concat_list, final_path)
    print(f"  ✅ Done! → {final_path}")

    return final_path


def collect_to_daily_folder(results: list[tuple[int, str]]):
    """Copy finished videos into a date-stamped folder (YYYY-MM-DD)."""
    today_str = date.today().strftime("%Y-%m-%d")
    daily_dir = OUTPUT_DIR / today_str
    daily_dir.mkdir(parents=True, exist_ok=True)

    for day, path in results:
        src = Path(path)
        dst = daily_dir / src.name
        shutil.copy2(src, dst)

    print(f"\n  Copied {len(results)} videos to: {daily_dir}")
    return daily_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_daily.py <start_day> [count]")
        print("  start_day   Starting day number")
        print("  count       Number of videos to generate (default: 7)")
        print()
        print("Examples:")
        print("  python3 generate_daily.py 1      # Day 1~7")
        print("  python3 generate_daily.py 8      # Day 8~14")
        print("  python3 generate_daily.py 15 3   # Day 15~17")
        sys.exit(1)

    start = int(sys.argv[1])
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    days = list(range(start, start + count))

    print(f"Generating {len(days)} videos (Day {days[0]} ~ Day {days[-1]})\n")

    # Load content plan to show topic names
    plan_path = DATA_DIR / "content_plan_365.csv"
    topics = {}
    if plan_path.exists():
        with open(plan_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                topics[int(row["day"])] = row["title_en"]

    results = []
    for day in days:
        topic = topics.get(day, "Unknown topic")
        print(f"\n  Day {day}: {topic}")
        path = generate_video_for_day(day)
        if path:
            results.append((day, path))

    # Collect into today's date folder
    if results:
        daily_dir = collect_to_daily_folder(results)

    print(f"\n{'='*50}")
    print(f"  Generated {len(results)} / {len(days)} videos")
    for day, path in results:
        print(f"  Day {day}: {path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
