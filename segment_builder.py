import subprocess

from config import TimingConfig, VideoConfig
from utils import get_audio_duration


def build_segment(
    index: int,
    frame_path: str,
    english_audio_path: str,
    korean_audio_path: str,
    output_path: str,
    timing: TimingConfig,
    video: VideoConfig,
) -> str:
    en_dur = get_audio_duration(english_audio_path)
    kr_dur = get_audio_duration(korean_audio_path)

    # Timeline:
    # [0 .. en_dur] english audio
    # [en_dur .. en_dur + think] silence
    # [kr1_start .. kr1_start + kr_dur] korean 1st
    # [kr1_end .. kr1_end + shadowing] silence
    # [kr2_start .. kr2_start + kr_dur] korean 2nd
    # [kr2_end .. kr2_end + transition] silence
    kr1_start = en_dur + timing.think_pause_sec
    kr2_start = kr1_start + kr_dur + timing.shadowing_pause_sec
    total_dur = kr2_start + kr_dur + timing.transition_sec

    kr1_delay_ms = int(kr1_start * 1000)
    kr2_delay_ms = int(kr2_start * 1000)

    # Use forward slashes for FFmpeg on Windows
    frame = frame_path.replace("\\", "/")
    en_audio = english_audio_path.replace("\\", "/")
    kr_audio = korean_audio_path.replace("\\", "/")
    out = output_path.replace("\\", "/")

    filter_complex = (
        f"[1:a]aformat=sample_rates={video.audio_sample_rate}:channel_layouts=stereo[en];"
        f"[2:a]aformat=sample_rates={video.audio_sample_rate}:channel_layouts=stereo,"
        f"asplit=2[kra][krb];"
        f"[kra]adelay={kr1_delay_ms}|{kr1_delay_ms}[kr1];"
        f"[krb]adelay={kr2_delay_ms}|{kr2_delay_ms}[kr2];"
        f"[en][kr1][kr2]amix=inputs=3:duration=longest:normalize=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(video.fps),
        "-t", f"{total_dur:.3f}", "-i", frame,
        "-i", en_audio,
        "-i", kr_audio,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", video.video_codec, "-crf", str(video.crf), "-preset", video.preset,
        "-c:a", video.audio_codec, "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed for segment {index}:\n{result.stderr[-500:]}"
        )

    return output_path
