import json
from types import SimpleNamespace
from pathlib import Path
from crate.probe import parse_ffprobe_json, probe, ProbeResult


_RAW = json.dumps({
    "format": {"duration": "300.5", "format_name": "matroska,webm"},
    "streams": [{"codec_type": "audio", "codec_name": "opus"}],
})


def test_parse():
    r = parse_ffprobe_json(_RAW)
    assert r.duration == 300.5
    assert r.codec == "opus"
    assert "webm" in r.container


def test_probe_uses_injected_runner():
    def fake_runner(argv, **kw):
        assert "ffprobe" in argv[0]
        return SimpleNamespace(stdout=_RAW, returncode=0)
    r = probe(Path("/x.webm"), runner=fake_runner)
    assert isinstance(r, ProbeResult)
    assert r.duration == 300.5
