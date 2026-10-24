from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProbeResult:
    duration: float
    codec: str
    container: str


def parse_ffprobe_json(raw: str) -> ProbeResult:
    data = json.loads(raw)
    fmt = data.get("format", {})
    duration = float(fmt.get("duration", 0.0) or 0.0)
    container = fmt.get("format_name", "")
    codec = ""
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            codec = stream.get("codec_name", "")
            break
    if not codec and data.get("streams"):
        codec = data["streams"][0].get("codec_name", "")
    return ProbeResult(duration=duration, codec=codec, container=container)


def probe(path: Path, runner=subprocess.run) -> ProbeResult:
    argv = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    proc = runner(argv, capture_output=True, text=True,
                  encoding="utf-8", errors="replace")
    return parse_ffprobe_json(proc.stdout)
