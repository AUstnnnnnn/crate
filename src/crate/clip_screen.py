from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Static, Footer
from textual.binding import Binding

from crate.config import Config
from crate.timecode import parse_timecode, format_timecode
from crate.library import clip_path
from crate.processor import build_clip_argv, run_ffmpeg


def validate_range(in_s: float, out_s: float, duration: float) -> None:
    if in_s < 0:
        raise ValueError("start before zero")
    if out_s <= in_s:
        raise ValueError("end must be after start")
    if duration and out_s > duration:
        raise ValueError("end past duration")


def export_clip(cfg: Config, source: Path, title: str,
                in_s: float, out_s: float, runner=subprocess.run) -> Path:
    dst = clip_path(cfg, title, in_s, out_s)
    dst.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(build_clip_argv(source, dst, in_s, out_s), runner=runner)
    return dst


class ClipScreen(Screen):
    BINDINGS = [
        Binding("p", "preview", "preview"),
        Binding("e", "export", "export"),
        Binding("escape", "app.pop_screen", "back"),
    ]

    def __init__(self, cfg: Config, source: Path, title: str, duration: float):
        super().__init__()
        self.cfg = cfg
        self.source = source
        self.clip_title = title
        self.duration = duration

    def compose(self) -> ComposeResult:
        yield Static(f"clip: {self.clip_title}  ({format_timecode(self.duration)})",
                     id="cliphead")
        yield Input(placeholder="in   e.g. 0:32", id="in")
        yield Input(placeholder="out  e.g. 0:40", id="out")
        yield Static("[p]review   [e]xport   [esc] back", id="clipstatus")
        yield Footer()

    def _range(self) -> tuple[float, float]:
        in_s = parse_timecode(self.query_one("#in", Input).value)
        out_s = parse_timecode(self.query_one("#out", Input).value)
        validate_range(in_s, out_s, self.duration)
        return in_s, out_s

    def action_preview(self) -> None:
        try:
            in_s, out_s = self._range()
            ext = self.cfg.sample_format
            tmp = Path(tempfile.gettempdir()) / f"crate_preview.{ext}"
            run_ffmpeg(build_clip_argv(self.source, tmp, in_s, out_s))
            subprocess.Popen(["afplay", str(tmp)])
            self.query_one("#clipstatus", Static).update("[cyan]previewing…[/]")
        except Exception as exc:
            self.query_one("#clipstatus", Static).update(f"[red]{exc}[/]")

    def action_export(self) -> None:
        try:
            in_s, out_s = self._range()
            out = export_clip(self.cfg, self.source, self.clip_title, in_s, out_s)
            self.query_one("#clipstatus", Static).update(
                f"[green]saved {out.name}[/]")
        except Exception as exc:
            self.query_one("#clipstatus", Static).update(f"[red]{exc}[/]")
