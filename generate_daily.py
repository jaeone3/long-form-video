"""Generate videos with auto state tracking.

Usage:
    python3 generate_daily.py [count]

Examples:
    python3 generate_daily.py       # Next 7 videos (auto)
    python3 generate_daily.py 3     # Next 3 videos
    python3 generate_daily.py 14    # Next 14 videos
"""
import os
import sys
import csv
import json
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
STATE_FILE = BASE_DIR / "state.json"


def load_state() -> dict:
    """Load generation state. Returns dict with next_day and round."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"next_day": 1, "round": 1, "history": []}


def save_state(next_day: int, round_num: int, generated: list[int]):
    """Save state with round tracking."""
    state = load_state()
    history = state.get("history", [])
    history.append({
        "date": date.today().isoformat(),
        "round": round_num,
        "days": generated,
    })
    STATE_FILE.write_text(json.dumps({
        "next_day": next_day,
        "round": round_num,
        "history": history,
    }, indent=2, ensure_ascii=False))


def generate_video_for_day(day: int, round_num: int = 1):
    """Generate one complete video for a given day number (1-365)."""

    # Check if CSV exists for this day
    csv_path = DATA_DIR / f"day{day:03d}.csv"
    if not csv_path.exists():
        print(f"  ⚠ CSV not found: {csv_path} — skipping Day {day}")
        return None

    # Create day-specific output folder (round prefix if round > 1)
    folder_name = f"day{day:03d}" if round_num == 1 else f"r{round_num}_day{day:03d}"
    day_dir = OUTPUT_DIR / folder_name
    for subdir in ["tts", "frames", "segments"]:
        (day_dir / subdir).mkdir(parents=True, exist_ok=True)

    timing = TimingConfig()
    video = VideoConfig()
    fonts = FontConfig()
    tts = TTSConfig()

    # Clear flag cache for fresh rendering
    _flag_cache.clear()

    # Get unique theme for this day + round
    theme = get_theme_for_day(day, round_num)

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
    final_name = f"day{day:03d}_final.mp4" if round_num == 1 else f"r{round_num}_day{day:03d}_final.mp4"
    final_path = str(day_dir / final_name)
    concatenate_segments(concat_list, final_path)
    print(f"  Done! -> {final_path}")

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
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    state = load_state()
    start = state["next_day"]
    round_num = state.get("round", 1)

    # Build day list, wrapping around 365 for new rounds
    days = []
    for i in range(count):
        day = start + i
        if day > 365:
            day = ((day - 1) % 365) + 1
            if i == 0:
                round_num += 1
        days.append(day)

    print(f"Round {round_num} — Generating {len(days)} videos (Day {days[0]} ~ Day {days[-1]})")
    print(f"State: next_day was {start}\n")

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
        path = generate_video_for_day(day, round_num)
        if path:
            results.append((day, path))

    # Collect into today's date folder
    if results:
        daily_dir = collect_to_daily_folder(results)

    # Save state — next day to generate
    next_day = start + len(days)
    next_round = round_num
    if next_day > 365:
        next_day = ((next_day - 1) % 365) + 1
        next_round += 1
    save_state(next_day, next_round, days)

    print(f"\n{'='*50}")
    print(f"  Generated {len(results)} / {len(days)} videos")
    for day, path in results:
        print(f"  Day {day}: {path}")
    print(f"  Next run: Round {next_round}, Day {next_day}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
