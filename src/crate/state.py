from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path("~/.config/crate/state.json").expanduser()


def save_items(items, path: Path | None = None) -> None:
    """Persist completed downloads (the ones with a real file) across sessions."""
    path = path or STATE_PATH
    keep = [
        {
            "url": i.url,
            "preset": i.preset,
            "title": i.title,
            "detail": i.detail,
            "path": str(i.path),
        }
        for i in items
        if i.status == "done" and i.path
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(keep, indent=2), encoding="utf-8")


def load_items(path: Path | None = None) -> list[dict]:
    # resolved per call, not bound at import — lets tests redirect STATE_PATH
    path = path or STATE_PATH
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []
