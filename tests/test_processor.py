from types import SimpleNamespace
from pathlib import Path
import pytest
from crate.processor import (
    build_clip_argv, build_extract_argv, run_ffmpeg, ProcessorError,
)


def test_clip_argv_is_sample_accurate():
    argv = build_clip_argv(Path("/a.webm"), Path("/o.wav"), 32.0, 40.0)
    i = argv.index("-i")
    # -ss must come AFTER -i for sample-accurate seeking
    assert argv.index("-ss") > i
    assert "-to" in argv
    assert argv[-1] == "/o.wav"


def test_extract_argv_no_normalize():
    argv = build_extract_argv(Path("/a.webm"), Path("/o.wav"), normalize=False)
    assert "loudnorm" not in " ".join(argv)
    assert argv[-1] == "/o.wav"


def test_extract_argv_with_normalize():
    argv = build_extract_argv(Path("/a.webm"), Path("/o.wav"), normalize=True)
    assert "loudnorm" in " ".join(argv)


def test_run_ffmpeg_raises_on_error():
    def fail(argv, **kw):
        return SimpleNamespace(returncode=1, stderr="boom")
    with pytest.raises(ProcessorError):
        run_ffmpeg(["ffmpeg"], runner=fail)


def test_run_ffmpeg_ok():
    def ok(argv, **kw):
        return SimpleNamespace(returncode=0, stderr="")
    run_ffmpeg(["ffmpeg"], runner=ok)  # no raise
