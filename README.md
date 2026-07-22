# crate

A terminal app for digging up media — download audio to sample, video to keep,
or whole files to archive. No sketchy ytmp3 mirrors, no popups, no viruses. Just
[yt-dlp](https://github.com/yt-dlp/yt-dlp) + [ffmpeg](https://ffmpeg.org),
wrapped in a fast TUI, running entirely on your machine.

```
◉ crate   dig · sample · archive
```

## What it does

- **Three presets, one Enter.** Paste a URL, pick a pad, hit Enter.
  - `archive` — best quality, original container, metadata + thumbnail embedded.
  - `sample` — audio extracted to WAV (lossless, sampler-ready).
  - `video` — best video + audio, merged to mp4.
- **Live queue.** Each download is its own row with live progress. One failed
  URL never takes down the others.
- **Clip trimming (the good part).** On any finished item, mark in/out
  timecodes, audition the slice with `afplay`, and export just that piece as a
  WAV — straight into your samples folder.
- **Metadata sidecar.** Every download drops a `.json` next to it (source URL,
  uploader, duration, timestamp) so the archive stays searchable.

Everything lands in an organized tree under your library root:

```
<library>/
  archive/<uploader>/<title>.<ext>
  samples/<title>.wav
  samples/clips/<title>_0.32-0.40.wav
  video/<title>.mp4
```

## Requirements

- Python 3.11+
- `ffmpeg` and `ffprobe` on your `PATH` (`brew install ffmpeg`)
- macOS for clip preview (`afplay`); downloads/exports work anywhere

## Install

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Run

```bash
./venv/bin/python -m crate
```

## Keys

| Key | Action |
|-----|--------|
| Enter | download the URL with the selected preset |
| ↑ / ↓ | pick preset pad / move in the queue |
| F3 | clip the selected finished item |
| F2 | advanced options (format, normalize, output override) — next download only |
| F4 | open the library folder |
| Ctrl+Q | quit |

**In the clip screen:** enter in/out timecodes (`0:32`, `1:04.5`), `p` to
preview the slice, `e` to export, `Esc` to go back.

## Config

`~/.config/crate/config.toml` (created with defaults on first run):

```toml
library_root = "~/Desktop/Dev/sounds"
default_preset = "sample"   # archive | sample | video
sample_format = "wav"       # wav | flac
normalize = false           # EBU R128 loudnorm on sample extract
filename_template = "%(title)s"
```

## Tests

```bash
./venv/bin/python -m pytest
```

Unit tests mock all external tools — no network, no ffmpeg. One live
end-to-end download is gated behind an env flag:

```bash
CRATE_LIVE_TEST=1 ./venv/bin/python -m pytest tests/test_live_smoke.py
```

## Notes / not yet

- A playlist URL downloads as a single queue row (the whole list), rather than
  expanding into one row per track. On the list for a later pass.
- Image/gallery sites (gallery-dl) and multi-connection acceleration (aria2)
  are intentionally out of v1.
