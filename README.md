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
- **Apple Music links resolve, not rip.** Paste a `music.apple.com` song link
  and crate reads its tags from Apple's public catalogue API, finds the same
  recording on a source it can actually download, and tags the file with
  Apple's artist/title. Album links fan out into one queue row per song.
  Apple's own streams are DRM-encrypted and are never touched; if a track is
  too obscure to exist anywhere else, crate falls back to Apple's public
  preview clip and names the file `<title> (preview)` so it is never mistaken
  for the full take.
- **Metadata travels with the file.** Title, artist, date, and source URL are
  embedded directly into each download (via ffmpeg) — no sidecar files.
- **Persistent crate.** Finished downloads stay in the list across sessions.
  Press Enter on any row to reveal that file in Finder / Explorer.
- **Live queue.** Each download is its own row with live progress. One failed
  URL never takes down the others.
- **Clip trimming (the good part).** On any finished item, mark in/out
  timecodes, audition the slice (`afplay` on macOS, `ffplay` elsewhere), and export just that piece as a
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
- `ffmpeg`, `ffprobe` (and `ffplay` for clip preview off macOS) on your `PATH`
  - macOS: `brew install ffmpeg`
  - Windows: `winget install Gyan.FFmpeg`, then open a new terminal
  - Linux: `sudo apt install ffmpeg` (or your distro's equivalent)

Runs on macOS, Windows (Windows Terminal recommended) and Linux.

## Install

```bash
git clone https://github.com/AUstnnnnnn/crate.git && cd crate
python3 -m venv venv
./venv/bin/pip install -e .        # installs deps + the `crate` command
ln -sf "$PWD/venv/bin/crate" ~/.local/bin/crate   # put it on your PATH
```

Windows (PowerShell):

```powershell
git clone https://github.com/AUstnnnnnn/crate.git; cd crate
py -m venv venv
venv\Scripts\pip install -e .
venv\Scripts\crate              # or add venv\Scripts to your PATH
```

Or skip the venv entirely with `pipx install git+https://github.com/AUstnnnnnn/crate.git`.

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
| Enter (on a row) | reveal that file in Finder / Explorer |
| F1 | show/hide the hint bar (remembered across sessions) |
| F3 | clip the selected finished item |
| F2 | advanced options (format, normalize, output override) — next download only |
| F4 | open the library folder |
| Ctrl+Q | quit |

**In the clip screen:** enter in/out timecodes (`0:32`, `1:04.5`), `p` to
preview the slice, `e` to export, `Esc` to go back.

## Config

`~/.config/crate/config.toml` (on Windows `%USERPROFILE%\.config\crate\config.toml`):

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
