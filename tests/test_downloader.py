from pathlib import Path
from crate.config import Config
from crate.downloader import (
    PRESET_FORMATS, build_ydl_opts, info_to_meta, expand_entries,
)


def _cfg(tmp_path):
    return Config(library_root=tmp_path, sample_format="wav")


def test_preset_formats_cover_all():
    assert set(PRESET_FORMATS) == {"library", "sample", "video"}


def test_build_opts_sample_adds_extract_postprocessor(tmp_path):
    opts = build_ydl_opts(_cfg(tmp_path), "sample", progress_hook=lambda d: None)
    assert opts["format"] == PRESET_FORMATS["sample"]
    pps = [p["key"] for p in opts.get("postprocessors", [])]
    assert "FFmpegExtractAudio" in pps


def test_build_opts_library_no_extract(tmp_path):
    opts = build_ydl_opts(_cfg(tmp_path), "library", progress_hook=lambda d: None)
    pps = [p["key"] for p in opts.get("postprocessors", [])]
    assert "FFmpegExtractAudio" not in pps


def test_build_opts_embeds_metadata(tmp_path):
    for preset in ("library", "sample", "video"):
        opts = build_ydl_opts(_cfg(tmp_path), preset, progress_hook=lambda d: None)
        pps = [p["key"] for p in opts.get("postprocessors", [])]
        assert "FFmpegMetadata" in pps


def test_info_to_meta():
    info = {"webpage_url": "http://x", "uploader": "Aphex",
            "title": "Xtal", "duration": 300, "ext": "webm"}
    meta = info_to_meta(info, "library")
    assert meta.title == "Xtal"
    assert meta.uploader == "Aphex"
    assert meta.preset == "library"


def test_expand_entries_playlist():
    info = {"entries": [{"title": "a"}, {"title": "b"}]}
    assert len(expand_entries(info)) == 2


def test_expand_entries_single():
    info = {"title": "solo"}
    assert expand_entries(info) == [info]
