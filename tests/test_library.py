from crate.config import Config
from crate.library import MediaMeta, sanitize, resolve_path, clip_path


def _cfg(tmp_path):
    return Config(library_root=tmp_path, sample_format="wav")


def test_sanitize_strips_separators():
    assert sanitize("a/b:c") == "a_b_c"
    assert "/" not in sanitize("Artist / Track")


def test_resolve_library(tmp_path):
    cfg = _cfg(tmp_path)
    meta = MediaMeta("u", "Aphex", "Xtal", 300.0, "library", "webm")
    assert resolve_path(cfg, meta) == tmp_path / "library" / "Aphex" / "Xtal.webm"


def test_resolve_sample(tmp_path):
    cfg = _cfg(tmp_path)
    meta = MediaMeta("u", "Aphex", "Xtal", 300.0, "sample", "wav")
    assert resolve_path(cfg, meta) == tmp_path / "samples" / "Xtal.wav"


def test_resolve_video(tmp_path):
    cfg = _cfg(tmp_path)
    meta = MediaMeta("u", "Aphex", "Xtal", 300.0, "video", "mp4")
    assert resolve_path(cfg, meta) == tmp_path / "video" / "Xtal.mp4"


def test_clip_path(tmp_path):
    cfg = _cfg(tmp_path)
    p = clip_path(cfg, "Xtal", 32.0, 40.0)
    assert p == tmp_path / "samples" / "clips" / "Xtal_0.32-0.40.wav"
