from __future__ import annotations

import inspect
import subprocess
from dataclasses import dataclass
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import (
    Footer, Input, DataTable, Static, RadioSet, RadioButton,
)

from crate.config import Config
from crate.library import resolve_path
from crate.probe import probe

_PRESETS = ("library", "sample", "video")
_GLYPH = {"queued": "·", "downloading": "▸", "done": "◉", "error": "✕"}

_BANNER = (
    "[b #e0a44a]◉ crate[/]   "
    "[#8a7d6d]dig · sample · library[/]"
)

CRATE_THEME = Theme(
    name="crate",
    primary="#e0a44a",     # vinyl-label amber
    secondary="#b5654a",   # clay
    accent="#7fae5f",      # crate-stamp green
    foreground="#ece3d3",  # warm off-white
    background="#14100c",  # roasted near-black
    surface="#1e1813",
    panel="#26201a",
    success="#7fae5f",
    warning="#e0a44a",
    error="#d9503f",
    dark=True,
    variables={
        "block-cursor-background": "#e0a44a",
        "block-cursor-foreground": "#14100c",
        "input-selection-background": "#b5654a 35%",
        "footer-key-foreground": "#e0a44a",
    },
)


def progress_to_fraction(d: dict) -> float:
    if d.get("status") == "finished":
        return 1.0
    total = d.get("total_bytes") or d.get("total_bytes_estimate")
    got = d.get("downloaded_bytes")
    if total and got:
        return max(0.0, min(1.0, got / total))
    return 0.0


@dataclass
class QueueItem:
    url: str
    preset: str
    title: str = ""
    status: str = "queued"
    progress: float = 0.0
    detail: str = ""
    row_key: object = None
    path: Path | None = None


class CrateApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "crate"
    SUB_TITLE = "dig for media"
    BINDINGS = [
        Binding("f2", "advanced", "advanced"),
        Binding("f3", "clip", "clip", priority=True),
        Binding("f4", "open_folder", "open folder", priority=True),
        Binding("ctrl+q", "quit", "quit", priority=True),
    ]

    def __init__(self, cfg: Config, download_fn=None):
        super().__init__()
        self.cfg = cfg
        self.items: list[QueueItem] = []
        self.current_preset = cfg.default_preset
        self.overrides = None
        self._download_fn = download_fn or self._real_download

    def compose(self) -> ComposeResult:
        yield Static(_BANNER, id="banner")
        with Vertical(id="body"):
            with Horizontal(id="urlbar"):
                yield Input(placeholder="paste a URL, press Enter…", id="url")
            with RadioSet(id="preset"):
                for name in _PRESETS:
                    yield RadioButton(name, value=(name == self.current_preset),
                                      id=f"preset-{name}")
            yield DataTable(id="queue", cursor_type="row")
            yield Static("crate's empty — paste a URL to start digging",
                         id="empty")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(CRATE_THEME)
        self.theme = "crate"
        table = self.query_one("#queue", DataTable)
        table.add_column("", width=2)
        table.add_column("title", width=44)
        table.add_column("preset", width=9)
        table.add_column("status", width=14)
        table.display = False
        from crate.advanced import missing_tools
        missing = missing_tools()
        if missing:
            self.notify(f"missing tools: {', '.join(missing)}",
                        severity="error", timeout=10)
        self.query_one("#url", Input).focus()

    # ── interaction ──────────────────────────────────────────────────────
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "preset":
            self.current_preset = _PRESETS[event.index]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url":
            self.action_download()

    def _effective_cfg(self) -> Config:
        return self.overrides.apply(self.cfg) if self.overrides else self.cfg

    def enqueue(self, url: str, preset: str) -> QueueItem:
        item = QueueItem(url=url, preset=preset, title=url)
        self.items.append(item)
        table = self.query_one("#queue", DataTable)
        self.query_one("#empty", Static).display = False
        table.display = True
        item.row_key = table.add_row(_GLYPH["queued"], item.title, preset, "queued")
        return item

    def action_download(self) -> None:
        url = self.query_one("#url", Input).value.strip()
        if not url:
            return
        item = self.enqueue(url, self.current_preset)
        self.query_one("#url", Input).value = ""
        self.run_worker(self._worker(item), exclusive=False)

    async def _worker(self, item: QueueItem) -> None:
        res = self._download_fn(item)
        if inspect.isawaitable(res):
            await res

    async def _real_download(self, item: QueueItem) -> None:
        import asyncio
        from crate.downloader import Downloader

        cfg = self._effective_cfg()
        item.status = "downloading"
        self._refresh_row(item)

        def hook(d):
            item.progress = progress_to_fraction(d)
            self.call_from_thread(self._refresh_row, item)

        try:
            staged, meta = await asyncio.to_thread(
                Downloader().download, item.url, cfg, item.preset, hook
            )
            dest = resolve_path(cfg, meta)
            dest.parent.mkdir(parents=True, exist_ok=True)
            staged.replace(dest)
            item.title = meta.title
            item.path = dest
            item.status = "done"
            item.detail = f"{dest.stat().st_size // 1024} KB"
        except Exception as exc:  # per-item isolation — never crash the app
            item.status = "error"
            item.detail = str(exc).splitlines()[0][:60]
        self._refresh_row(item)

    def _refresh_row(self, item: QueueItem) -> None:
        table = self.query_one("#queue", DataTable)
        cols = table.ordered_columns
        if item.status == "downloading":
            status_txt = f"{int(item.progress * 100)}%"
        elif item.detail:
            status_txt = item.detail
        else:
            status_txt = item.status
        table.update_cell(item.row_key, cols[0].key, _GLYPH[item.status])
        table.update_cell(item.row_key, cols[1].key, item.title)
        table.update_cell(item.row_key, cols[2].key, item.preset)
        table.update_cell(item.row_key, cols[3].key, status_txt)

    # ── actions ──────────────────────────────────────────────────────────
    def action_clip(self) -> None:
        if not self.items:
            return
        table = self.query_one("#queue", DataTable)
        item = self.items[table.cursor_row]
        if item.status != "done" or not item.path:
            return
        from crate.clip_screen import ClipScreen
        dur = probe(item.path).duration if item.path.exists() else 0.0
        self.push_screen(
            ClipScreen(self._effective_cfg(), item.path, item.title, dur)
        )

    def action_advanced(self) -> None:
        from crate.advanced import AdvancedScreen

        def _store(ov):
            self.overrides = ov

        self.push_screen(AdvancedScreen(self.cfg), _store)

    def action_open_folder(self) -> None:
        subprocess.run(["open", str(self._effective_cfg().library_root)],
                       check=False)
