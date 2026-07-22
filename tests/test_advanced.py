from pathlib import Path
from crate.config import Config
from crate.advanced import Overrides, missing_tools


def test_overrides_apply(tmp_path):
    cfg = Config(library_root=tmp_path, sample_format="wav", normalize=False)
    new = Overrides(sample_format="flac", normalize=True, output_dir=None).apply(cfg)
    assert new.sample_format == "flac"
    assert new.normalize is True
    assert cfg.sample_format == "wav"  # original untouched


def test_overrides_none_keeps(tmp_path):
    cfg = Config(library_root=tmp_path, sample_format="wav")
    new = Overrides(None, None, None).apply(cfg)
    assert new.sample_format == "wav"


def test_missing_tools(monkeypatch):
    import crate.advanced as adv
    monkeypatch.setattr(adv.shutil, "which",
                        lambda name: None if name == "ffmpeg" else "/x")
    assert "ffmpeg" in missing_tools()
    assert "ffprobe" not in missing_tools()
