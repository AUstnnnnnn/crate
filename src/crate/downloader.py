from __future__ import annotations

from pathlib import Path

from crate.applemusic import (
    AppleMusicError, AppleTrack, is_apple_url, parse_apple_url, resolve,
    search_query,
)
from crate.config import Config
from crate.library import MediaMeta

PRESET_FORMATS = {
    "library": "bestvideo+bestaudio/best",
    "sample": "bestaudio/best",
    "video": "bestvideo[ext=mp4]+bestaudio/best/best",
}


# how many search hits to consider, and how far a runtime may drift from the
# one Apple reports before we stop trusting the match
SEARCH_COUNT = 5
DURATION_TOLERANCE = 15.0


class _SilentLogger:
    """Swallow yt-dlp console output so it never corrupts the TUI."""

    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def build_ydl_opts(cfg: Config, preset: str, progress_hook) -> dict:
    staging = cfg.library_root / ".staging"
    opts: dict = {
        "format": PRESET_FORMATS[preset],
        "outtmpl": str(staging / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _SilentLogger(),
    }
    pps: list[dict] = []
    if preset == "sample":
        pps.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": cfg.sample_format,
        })
    elif preset == "video":
        opts["merge_output_format"] = "mp4"
    # embed title/artist/date/etc into the file itself — no sidecar
    pps.append({"key": "FFmpegMetadata"})
    opts["postprocessors"] = pps
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


def pick_search_entry(entries: list[dict], target: float) -> dict | None:
    """Top hit, unless one further down actually matches Apple's runtime."""
    entries = [e for e in entries if e]
    if not entries or not target:
        return entries[0] if entries else None
    for e in entries:
        if abs(float(e.get("duration") or 0) - target) <= DURATION_TOLERANCE:
            return e
    return entries[0]


def apple_meta(track: AppleTrack, preset: str, ext: str, preview: bool) -> MediaMeta:
    """Apple's tagging beats whatever the uploader typed on the search source."""
    return MediaMeta(
        source_url=track.source_url,
        uploader=track.artist,
        title=f"{track.title} (preview)" if preview else track.title,
        duration=track.duration,
        preset=preset,
        ext=ext,
    )


class Downloader:
    """Integration wrapper around yt_dlp.YoutubeDL (not unit-tested)."""

    @staticmethod
    def _staged_path(ydl, entry: dict) -> Path:
        # requested_downloads carries the real post-processed path
        # (e.g. the .wav after FFmpegExtractAudio), unlike prepare_filename.
        reqs = entry.get("requested_downloads")
        if reqs:
            return Path(reqs[-1]["filepath"])
        return Path(ydl.prepare_filename(entry))

    def download(
        self, url: str, cfg: Config, preset: str, progress_hook
    ) -> tuple[Path, MediaMeta]:
        if is_apple_url(url):
            return self._download_apple(url, cfg, preset, progress_hook)

        import yt_dlp  # local import: keeps module importable without the dep

        opts = build_ydl_opts(cfg, preset, progress_hook)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            entry = expand_entries(info)[0]
            meta = info_to_meta(entry, preset)
            return self._staged_path(ydl, entry), meta

    def _download_apple(
        self, url: str, cfg: Config, preset: str, progress_hook
    ) -> tuple[Path, MediaMeta]:
        """Apple's own stream is DRM-locked; we match the song elsewhere.

        Apple supplies the tags, a search source supplies the audio. If nothing
        out there has the song, we fall back to Apple's public preview clip and
        label it as one so a 90-second file is never mistaken for the full take.
        """
        import yt_dlp

        if parse_apple_url(url).kind == "album":
            raise AppleMusicError("album link — queue its songs individually")
        track = resolve(url)[0]

        opts = build_ydl_opts(cfg, preset, progress_hook)
        with yt_dlp.YoutubeDL(opts) as ydl:
            entry = None
            try:
                hits = ydl.extract_info(
                    f"ytsearch{SEARCH_COUNT}:{search_query(track)}",
                    download=False,
                )
                entry = pick_search_entry(expand_entries(hits), track.duration)
            except Exception:
                entry = None  # no hits, or the search source refused us

            if entry is not None:
                info = ydl.extract_info(
                    entry.get("webpage_url") or entry["url"], download=True)
                got = expand_entries(info)[0]
                path = self._staged_path(ydl, got)
                return path, apple_meta(track, preset, path.suffix.lstrip("."),
                                        preview=False)

            if not track.preview_url:
                raise AppleMusicError(
                    f"no source found for '{search_query(track)}' and Apple "
                    "offers no preview clip")
            info = ydl.extract_info(track.preview_url, download=True)
            got = expand_entries(info)[0]
            path = self._staged_path(ydl, got)
            return path, apple_meta(track, preset, path.suffix.lstrip("."),
                                    preview=True)
