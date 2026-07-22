from types import SimpleNamespace
from pathlib import Path
import pytest
from crate.config import Config
from crate.clip_screen import validate_range, export_clip


def test_validate_ok():
    validate_range(10, 20, 300)  # no raise


@pytest.mark.parametrize("a,b,dur", [(20, 10, 300), (0, 400, 300), (-1, 5, 300)])
def test_validate_bad(a, b, dur):
    with pytest.raises(ValueError):
        validate_range(a, b, dur)


def test_export_clip_uses_runner(tmp_path):
    cfg = Config(library_root=tmp_path, sample_format="wav")
    calls = []

    def runner(argv, **kw):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="")

    out = export_clip(cfg, Path("/src.webm"), "Xtal", 32.0, 40.0, runner=runner)
    assert out == tmp_path / "samples" / "clips" / "Xtal_0.32-0.40.wav"
    assert calls and "ffmpeg" in calls[0][0]
