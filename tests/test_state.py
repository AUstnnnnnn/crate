from pathlib import Path
from crate.state import save_items, load_items


class _Item:
    def __init__(self, status, path, title="t", url="u", preset="sample", detail="1 KB"):
        self.status, self.path, self.title = status, path, title
        self.url, self.preset, self.detail = url, preset, detail


def test_saves_only_done_with_path(tmp_path):
    p = tmp_path / "state.json"
    items = [
        _Item("done", tmp_path / "a.wav"),
        _Item("error", None),
        _Item("downloading", None),
        _Item("done", None),  # done but no path -> skipped
    ]
    save_items(items, p)
    recs = load_items(p)
    assert len(recs) == 1
    assert recs[0]["path"] == str(tmp_path / "a.wav")
    assert recs[0]["title"] == "t"


def test_load_missing_returns_empty(tmp_path):
    assert load_items(tmp_path / "nope.json") == []


def test_load_corrupt_returns_empty(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("{ not json")
    assert load_items(p) == []


def test_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    save_items([_Item("done", tmp_path / "x.mp4", title="Song", preset="video")], p)
    recs = load_items(p)
    assert recs[0]["preset"] == "video"
    assert recs[0]["title"] == "Song"
