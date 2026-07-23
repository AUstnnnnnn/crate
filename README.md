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
  - `library` — best quality, original container, kept by uploader.
  - `sample` — audio extracted to WAV (lossless, sampler-ready).
  - `video` — best video + audio, merged to mp4.
- **Metadata travels with the file.** Title, artist, date, and source URL are
  embedded directly into each download (via ffmpeg) — no sidecar files.
- **Persistent crate.** Finished downloads stay in the list across sessions.
  Press Enter on any row to reveal that file in Finder.
- **Live queue.** Each download is its own row with live progress. One failed
  URL never takes down the others.
- **Clip trimming (the good part).** On any finished item, mark in/out
  timecodes, audition the slice with `afplay`, and export just that piece as a
  WAV — straight into your samples folder.

Everything lands in an organized tree under your library root:

```
<library>/
  library/<uploader>/<title>.<ext>
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
./venv/bin/pip install -e .        # installs deps + the `crate` command
ln -sf "$PWD/venv/bin/crate" ~/.local/bin/crate   # put it on your PATH
```

## Run

```bash
crate                       # from anywhere
# or, without the PATH symlink:
./venv/bin/python -m crate
```

## Keys

| Key | Action |
|-----|--------|
| Enter (URL field) | download the URL with the selected preset |
| ◄ / ► | switch mode (library / sample / video) |
| ↑ / ↓ | move in the queue |
| Enter (on a row) | reveal that file in Finder |
| F3 | clip the selected finished item |
| F2 | advanced options (format, normalize, output override) — next download only |
| F4 | open the library folder |
| Ctrl+Q | quit |

**In the clip screen:** enter in/out timecodes (`0:32`, `1:04.5`), `p` to
preview the slice, `e` to export, `Esc` to go back.

## Config

`~/.config/crate/config.toml` (created with defaults on first run):

```toml
library_root = "~/Desktop/crate"
default_preset = "sample"   # library | sample | video
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
