from pathlib import Path
from crate.config import Config
from crate.downloader import (
    PRESET_FORMATS, build_ydl_opts, info_to_meta, expand_entries,
)


def _cfg(tmp_path):
    return Config(library_root=tmp_path, sample_format="wav")


def test_preset_formats_cover_all():
    assert set(PRESET_FORMATS) == {"archive", "sample", "video"}


def test_build_opts_sample_adds_extract_postprocessor(tmp_path):
    opts = build_ydl_opts(_cfg(tmp_path), "sample", progress_hook=lambda d: None)
    assert opts["format"] == PRESET_FORMATS["sample"]
    pps = [p["key"] for p in opts.get("postprocessors", [])]
    assert "FFmpegExtractAudio" in pps


def test_build_opts_archive_no_extract(tmp_path):
    opts = build_ydl_opts(_cfg(tmp_path), "archive", progress_hook=lambda d: None)
    pps = [p["key"] for p in opts.get("postprocessors", [])]
    assert "FFmpegExtractAudio" not in pps


def test_info_to_meta():
    info = {"webpage_url": "http://x", "uploader": "Aphex",
            "title": "Xtal", "duration": 300, "ext": "webm"}
    meta = info_to_meta(info, "archive")
    assert meta.title == "Xtal"
    assert meta.uploader == "Aphex"
    assert meta.preset == "archive"


def test_expand_entries_playlist():
    info = {"entries": [{"title": "a"}, {"title": "b"}]}
    assert len(expand_entries(info)) == 2


def test_expand_entries_single():
    info = {"title": "solo"}
    assert expand_entries(info) == [info]
