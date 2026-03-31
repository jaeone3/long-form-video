import subprocess


def create_concat_list(segment_paths: list[str], output_path: str) -> str:
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segment_paths:
            safe_path = seg.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
    return output_path


def concatenate_segments(concat_list_path: str, output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path.replace("\\", "/"),
        "-c", "copy",
        output_path.replace("\\", "/"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed:\n{result.stderr[-500:]}")

    return output_path
