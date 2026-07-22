from __future__ import annotations

import shutil
from dataclasses import dataclass, replace
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Checkbox, Input, Static, Footer
from textual.binding import Binding

from crate.config import Config


@dataclass
class Overrides:
    sample_format: str | None = None
    normalize: bool | None = None
    output_dir: Path | None = None

    def apply(self, cfg: Config) -> Config:
        changes: dict = {}
        if self.sample_format is not None:
            changes["sample_format"] = self.sample_format
        if self.normalize is not None:
            changes["normalize"] = self.normalize
        if self.output_dir is not None:
            changes["library_root"] = self.output_dir
        return replace(cfg, **changes)


def missing_tools() -> list[str]:
    return [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]


class AdvancedScreen(Screen):
    BINDINGS = [Binding("escape", "save", "save & back")]

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg

    def compose(self) -> ComposeResult:
        yield Static("advanced — applies to next download", id="advhead")
        yield Input(value=self.cfg.sample_format, placeholder="sample format",
                    id="fmt")
        yield Checkbox("normalize (loudnorm)", value=self.cfg.normalize, id="norm")
        yield Input(placeholder="output dir override", id="outdir")
        yield Static("[esc] save & back", id="advstatus")
        yield Footer()

    def current_overrides(self) -> Overrides:
        outdir = self.query_one("#outdir", Input).value.strip()
        return Overrides(
            sample_format=self.query_one("#fmt", Input).value.strip() or None,
            normalize=self.query_one("#norm", Checkbox).value,
            output_dir=Path(outdir).expanduser() if outdir else None,
        )

    def action_save(self) -> None:
        self.dismiss(self.current_overrides())
