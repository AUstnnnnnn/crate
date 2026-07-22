# crate — media-digging TUI

**Date:** 2026-07-22
**Status:** Approved design

A terminal UI for downloading media (audio, video, full archives) from the web
for sampling and archiving. Replaces sketchy ytmp3/SoundCloud-downloader sites by
wrapping the tools that already do the job well: yt-dlp, ffmpeg.

## Goals

- Paste a URL, get clean media out, with as few keystrokes as possible.
- Three first-class use cases: **archive** whole media, extract **audio samples**,
  keep **video**.
- **In-TUI clip trimming** — mark in/out points, audition, export a slice as a
  sampler-ready WAV. Headline feature.
- No viruses, no popups, no ads. Everything runs locally.

## Non-Goals (v1)

- Image/gallery downloads (gallery-dl) — later.
- aria2 multi-connection acceleration — later.
- Visual waveform rendering in the terminal — later.
- Batch/queued clip operations — v1 clips one item at a time.

## Stack

- **Python 3** + [Textual](https://textual.textualize.io) async TUI framework.
- **yt-dlp as a library** (`import yt_dlp`), not the CLI — lets us register
  progress hooks and drive real live progress bars instead of scraping stdout.
- **ffmpeg / ffprobe** for post-processing (audio extract, convert, loudnorm,
  clip slicing) and probing.
- macOS **`afplay`** for clip audition preview.
- Dependencies pinned in `requirements.txt`; project runs in a local venv.

Rationale: yt-dlp is Python, so a library binding is strictly better than
shelling out. ffmpeg is the standard post-processor and yt-dlp already integrates
with it. Node+Ink or Rust/Go would all shell out to yt-dlp — clumsier and, for
Rust/Go, not currently installed on this machine.

## Architecture

Small, single-purpose modules communicating through explicit interfaces so each
can be understood and unit-tested in isolation.

| Module | Responsibility | Depends on |
|---|---|---|
| `app.py` | Textual app, screens, key bindings, queue state | all below |
| `downloader.py` | Wrap `yt_dlp.YoutubeDL`; format selection; progress hooks; playlist expansion | yt_dlp |
| `processor.py` | ffmpeg ops: extract audio, convert, loudnorm, clip slice | ffmpeg (subprocess) |
| `probe.py` | ffprobe → duration, codec, container, tags | ffprobe (subprocess) |
| `library.py` | Resolve output paths, build folder tree, write metadata sidecar | config |
| `config.py` | Load/save TOML config; presets; defaults | — |
| `timecode.py` | Parse/format timecodes (`0:32`, `1:04.5`, `92`) ↔ seconds | — |

`downloader`, `processor`, `probe` are each wrapped behind a thin interface so the
TUI and tests depend on the interface, not the external tool. This keeps network
and ffmpeg out of unit tests (mocked) and confines all subprocess handling.

## Presets (smart defaults, one key each)

| Key | Preset | Behavior | Output |
|---|---|---|---|
| `a` | Archive | Best quality, keep original container, embed metadata + thumbnail | `<root>/archive/<uploader>/<title>.<ext>` |
| `s` | Sample | Extract audio → WAV (lossless, sampler-ready); optional loudnorm | `<root>/samples/<title>.wav` |
| `v` | Video | Best video+audio, merged to mp4 | `<root>/video/<title>.mp4` |

- Paste URL → press a preset key (or Enter for the configured default) → download.
- `Tab` opens an **advanced overlay** (format, quality cap, output-dir override,
  normalize toggle, WAV/FLAC) — only surfaced when the user wants it.
- Playlists auto-expand: each entry becomes its own queue row using the chosen
  preset.

## Screens

**Main screen**

```
┌ crate ───────────────────────────────────┐
│ URL ▸ [ paste here…            ] [a]rchive │
│                                  [s]ample  │
│                                  [v]ideo   │
├ Queue ────────────────────────────────────┤
│ ✓ Aphex Twin - Xtal        sample  3.2MB  │
│ ⣾ Boards of Canada - ...   archive ▓▓ 50% │
│ ⏸ playlist item 3/12       video   queued │
├───────────────────────────────────────────┤
│ [c]lip  [Tab]advanced  [o]pen folder  [q] │
└───────────────────────────────────────────┘
```

- URL input with paste support. Preset keys trigger a download of the current URL.
- Queue list: one row per item. Row shows status glyph, title, preset, and either
  live progress (%/speed/ETA) or final size / inline error.
- Footer: contextual key bindings.

**Clip screen** (`c` on a finished item) — headline feature

- Shows the item's duration and a text timeline.
- User enters in/out timecodes (`0:32`–`0:40`), parsed by `timecode.py`.
- `p` previews the slice via `afplay` (loops so a one-shot/loop can be auditioned).
- `e` exports: ffmpeg `-ss <in> -to <out>`, re-encoded sample-accurate to WAV →
  `<root>/samples/clips/<title>_<in>-<out>.wav`.
- `Esc` returns to main screen.

**Advanced overlay** (`Tab`) — modal over main screen

- Format / quality cap / output-dir override / normalize toggle / WAV vs FLAC.
- Applies to the next download; does not change saved defaults unless pinned.

## Data Flow

1. User pastes URL, presses preset key.
2. `app` calls `downloader.probe_or_expand(url)` → single item or playlist entries.
3. Each item added to queue; `downloader.download(item, preset)` runs async with a
   progress hook updating that row.
4. On completion, `processor` applies preset post-processing (audio extract,
   loudnorm, merge) as needed.
5. `library` moves the result to its resolved path and writes a `.json` metadata
   sidecar (source URL, uploader, title, duration, download timestamp, preset).
6. Row marked done with final size. Item eligible for clip mode.

## Error Handling

- Each queue item is fully isolated. A failed URL (geo-block, private, 404,
  unsupported) captures the yt-dlp error and shows it inline on that row.
- One failure never crashes the app or affects other in-flight/queued downloads.
- Missing external tool (ffmpeg not found) → clear startup check with a message,
  not a stack trace.
- Config parse errors fall back to defaults with a warning line.

## Config

`~/.config/crate/config.toml`:

```toml
library_root = "~/Desktop/Dev/sounds"
default_preset = "sample"        # a=archive, s=sample, v=video
sample_format = "wav"            # wav | flac
normalize = false                # EBU R128 loudnorm on sample extract
filename_template = "%(title)s"
```

- Library root defaults to `~/Desktop/Dev/sounds` (existing folder).
- Created with defaults on first run if absent.

## Testing

- **pytest** on pure logic: `timecode` parsing/formatting, `library` path
  resolution + sidecar shape, `config` load/save/defaults, format-string building
  in `downloader`.
- External tools mocked via their interfaces — no network, no ffmpeg in unit tests.
- One optional **live smoke test** (real short download) gated behind an env flag
  (e.g. `CRATE_LIVE_TEST=1`), excluded from the default run.

## Build Order (high level)

1. Project scaffold: venv, `requirements.txt`, package layout, config module.
2. `timecode` + `library` + tests (pure logic, no deps).
3. `probe` + `downloader` interfaces with mocks + tests; then real yt-dlp binding.
4. `processor` (audio extract, convert, loudnorm, clip) + tests with mocks.
5. Textual `app`: main screen, URL input, preset keys, queue with live progress.
6. Advanced overlay.
7. Clip screen with `afplay` preview + ffmpeg export.
8. Visual polish pass (frontend-design / impeccable) on the TUI.
9. README + first live smoke test.
