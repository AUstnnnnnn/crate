from __future__ import annotations

from pathlib import Path

from crate.config import Config
from crate.library import MediaMeta

PRESET_FORMATS = {
    "archive": "bestvideo+bestaudio/best",
    "sample": "bestaudio/best",
    "video": "bestvideo[ext=mp4]+bestaudio/best/best",
}


def build_ydl_opts(cfg: Config, preset: str, progress_hook) -> dict:
    staging = cfg.library_root / ".staging"
    opts: dict = {
        "format": PRESET_FORMATS[preset],
        "outtmpl": str(staging / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
    }
    if preset == "sample":
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": cfg.sample_format,
        }]
    elif preset == "video":
        opts["merge_output_format"] = "mp4"
    return opts


def info_to_meta(info: dict, preset: str) -> MediaMeta:
    return MediaMeta(
        source_url=info.get("webpage_url", info.get("original_url", "")),
        uploader=info.get("uploader", "unknown"),
        title=info.get("title", "untitled"),
        duration=float(info.get("duration") or 0.0),
        preset=preset,
        ext=info.get("ext", "bin"),
    )


def expand_entries(info: dict) -> list[dict]:
    if info.get("entries") is not None:
        return list(info["entries"])
    return [info]


class Downloader:
    """Integration wrapper around yt_dlp.YoutubeDL (not unit-tested)."""

    def download(
        self, url: str, cfg: Config, preset: str, progress_hook
    ) -> tuple[Path, MediaMeta]:
        import yt_dlp  # local import: keeps module importable without the dep

        opts = build_ydl_opts(cfg, preset, progress_hook)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            entry = expand_entries(info)[0]
            meta = info_to_meta(entry, preset)
            # requested_downloads carries the real post-processed path
            # (e.g. the .wav after FFmpegExtractAudio), unlike prepare_filename.
            reqs = entry.get("requested_downloads")
            if reqs:
                path = Path(reqs[-1]["filepath"])
            else:
                path = Path(ydl.prepare_filename(entry))
            return path, meta
