import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import ffmpeg

SUPPORTED_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}


def normalize_audio(input_path: str, target_ext: str = ".wav") -> Optional[str]:
    src = Path(input_path)
    if not src.exists():
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=target_ext) as tmp:
        tmp_path = Path(tmp.name)
    try:
        (
            ffmpeg
            .input(str(src))
            .output(str(tmp_path), ar=16000, ac=1)
            .overwrite_output()
            .run(quiet=True)
        )
        return str(tmp_path)
    except ffmpeg.Error:
        if tmp_path.exists():
            tmp_path.unlink()
        return None


def cleanup_file(path: str):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def extract_audio_from_media(input_path: str, target_ext: str = ".wav") -> Optional[str]:
    """
    從影片或其他複合媒體抽取音訊並轉為指定格式。
    """
    src = Path(input_path)
    if not src.exists():
        return None


def convert_to_voice_ogg(input_path: str) -> Optional[str]:
    """
    將音訊轉成 Telegram voice (OGG/Opus) 格式，方便顯示語音訊息圖示。
    """
    src = Path(input_path)
    if not src.exists():
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
        tmp_path = Path(tmp.name)
    try:
        (
            ffmpeg
            .input(str(src))
            .output(str(tmp_path), ac=1, ar=48000, codec="libopus", **{"vn": None})
            .overwrite_output()
            .run(quiet=True)
        )
        return str(tmp_path)
    except ffmpeg.Error:
        if tmp_path.exists():
            tmp_path.unlink()
        return None


def extract_video_frames(input_path: str, fps: int = 1, max_frames: int = 3) -> list[str]:
    """
    從影片中平均擷取多張影格 (jpeg)，以供 Vision 分析使用。
    """
    src = Path(input_path)
    if not src.exists() or max_frames <= 0:
        return []
    temp_dir = Path(tempfile.mkdtemp())
    pattern = temp_dir / "frame_%03d.jpg"
    frame_paths: list[str] = []
    try:
        (
            ffmpeg
            .input(str(src))
            .filter("fps", fps=fps)
            .output(str(pattern), vframes=max_frames)
            .overwrite_output()
            .run(quiet=True)
        )
        for frame_file in sorted(temp_dir.glob("frame_*.jpg")):
            if frame_file.stat().st_size > 0:
                frame_paths.append(str(frame_file))
            if len(frame_paths) >= max_frames:
                break
    except ffmpeg.Error:
        frame_paths = []
    if not frame_paths:
        for frame_file in temp_dir.glob("*"):
            frame_file.unlink(missing_ok=True)
        temp_dir.rmdir()
    return frame_paths
    with tempfile.NamedTemporaryFile(delete=False, suffix=target_ext) as tmp:
        tmp_path = Path(tmp.name)
    try:
        (
            ffmpeg
            .input(str(src))
            .output(str(tmp_path), ac=1, ar=16000, **{"vn": None})
            .overwrite_output()
            .run(quiet=True)
        )
        return str(tmp_path)
    except ffmpeg.Error:
        if tmp_path.exists():
            tmp_path.unlink()
        return None
