from pathlib import Path
from crate.config import Config, load_config, save_config


def test_load_returns_defaults_when_missing(tmp_path):
    cfg = load_config(tmp_path / "nope.toml")
    assert cfg.default_preset == "sample"
    assert cfg.sample_format == "wav"
    assert cfg.normalize is False
    assert isinstance(cfg.library_root, Path)
    assert cfg.library_root.is_absolute()


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "config.toml"
    cfg = Config(
        library_root=Path("~/music").expanduser(),
        default_preset="archive",
        sample_format="flac",
        normalize=True,
        filename_template="%(title)s",
    )
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.default_preset == "archive"
    assert loaded.sample_format == "flac"
    assert loaded.normalize is True


def test_library_root_is_expanded(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('library_root = "~/Desktop/Dev/sounds"\n')
    cfg = load_config(p)
    assert "~" not in str(cfg.library_root)
    assert cfg.library_root.is_absolute()
