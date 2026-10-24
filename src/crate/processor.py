from __future__ import annotations

import subprocess
from pathlib import Path


class ProcessorError(RuntimeError):
    pass


def build_clip_argv(src: Path, dst: Path, in_s: float, out_s: float) -> list[str]:
    # -ss after -i => sample-accurate (slower but exact) seek.
    return [
        "ffmpeg", "-hide_banner", "-y",
        "-i", str(src),
        "-ss", f"{in_s}", "-to", f"{out_s}",
        "-vn",
        str(dst),
    ]


def build_extract_argv(src: Path, dst: Path, normalize: bool) -> list[str]:
    argv = ["ffmpeg", "-hide_banner", "-y", "-i", str(src), "-vn"]
    if normalize:
        argv += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
    argv.append(str(dst))
    return argv


def run_ffmpeg(argv: list[str], runner=subprocess.run) -> None:
    proc = runner(argv, capture_output=True, text=True,
                  encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise ProcessorError(getattr(proc, "stderr", "") or "ffmpeg failed")
