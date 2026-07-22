from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from crate.config import Config
from crate.timecode import format_slug

_UNSAFE = re.compile(r'[/\\:\*\?"<>\|]')


@dataclass
class MediaMeta:
    source_url: str
    uploader: str
    title: str
    duration: float
    preset: str
    ext: str


def sanitize(name: str) -> str:
    cleaned = _UNSAFE.sub("_", name)
    return cleaned.strip().strip(".") or "untitled"


def resolve_path(cfg: Config, meta: MediaMeta) -> Path:
    root = cfg.library_root
    title = sanitize(meta.title)
    if meta.preset == "archive":
        return root / "archive" / sanitize(meta.uploader) / f"{title}.{meta.ext}"
    if meta.preset == "sample":
        return root / "samples" / f"{title}.{cfg.sample_format}"
    if meta.preset == "video":
        return root / "video" / f"{title}.mp4"
    raise ValueError(f"unknown preset: {meta.preset}")


def clip_path(cfg: Config, title: str, in_s: float, out_s: float) -> Path:
    title = sanitize(title)
    stem = f"{title}_{format_slug(in_s)}-{format_slug(out_s)}"
    return cfg.library_root / "samples" / "clips" / f"{stem}.{cfg.sample_format}"


def write_sidecar(path: Path, meta: MediaMeta) -> Path:
    side = path.with_suffix(path.suffix + ".json")
    data = asdict(meta)
    data["downloaded_at"] = datetime.now(timezone.utc).isoformat()
    side.parent.mkdir(parents=True, exist_ok=True)
    side.write_text(json.dumps(data, indent=2))
    return side
