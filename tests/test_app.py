import pytest
from textual.widgets import Input
from crate.config import Config
from crate.app import CrateApp, QueueItem


def test_queueitem_defaults():
    it = QueueItem(url="http://x", preset="sample")
    assert it.status == "queued"
    assert it.progress == 0.0


@pytest.mark.asyncio
async def test_enter_enqueues_with_default_preset(tmp_path):
    cfg = Config(library_root=tmp_path)  # default_preset == "sample"
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        app.query_one("#url", Input).value = "http://example.com/x"
        app.query_one("#url", Input).focus()
        await pilot.press("enter")
        assert len(app.items) == 1
        assert app.items[0].preset == "sample"
        assert app.query_one("#url", Input).value == ""


@pytest.mark.asyncio
async def test_arrows_cycle_presets(tmp_path):
    cfg = Config(library_root=tmp_path)  # starts on "sample" (index 1)
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        assert app.current_preset == "sample"
        await pilot.press("right")
        assert app.current_preset == "video"
        await pilot.press("right")  # wraps
        assert app.current_preset == "library"
        await pilot.press("left")
        assert app.current_preset == "video"


@pytest.mark.asyncio
async def test_empty_url_does_not_enqueue(tmp_path):
    cfg = Config(library_root=tmp_path)
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        app.query_one("#url", Input).focus()
        await pilot.press("enter")
        assert app.items == []


@pytest.mark.asyncio
async def test_f1_toggles_and_persists_hints(tmp_path, monkeypatch):
    import crate.config as cfgmod
    saved = {}
    monkeypatch.setattr(cfgmod, "save_config", lambda c, p=None: saved.update(show=c.show_hints))
    from textual.widgets import Footer
    cfg = Config(library_root=tmp_path)
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        assert app.query_one(Footer).display is True
        await pilot.press("f1")
        assert app.cfg.show_hints is False
        assert app.query_one(Footer).display is False
        assert saved["show"] is False


def test_error_detail_strips_ytdlp_prefix():
    exc = RuntimeError("ERROR: unable to download video data: HTTP Error 403: Forbidden\ntrace")
    from crate.app import error_detail
    assert error_detail(exc) == "unable to download video data: HTTP Error 403: Forbidden"


def test_error_detail_falls_back_to_type_name():
    from crate.app import error_detail
    assert error_detail(ValueError("")) == "ValueError"


@pytest.mark.asyncio
async def test_apple_album_link_expands_into_one_row_per_song(tmp_path, monkeypatch):
    import crate.applemusic as am
    from crate.applemusic import AppleTrack
    tracks = [
        AppleTrack("Xtal", "Aphex Twin", "SAW", 294.0, "", "https://music.apple.com/us/album/a/1?i=2"),
        AppleTrack("Ageispolis", "Aphex Twin", "SAW", 300.0, "", "https://music.apple.com/us/album/a/1?i=3"),
    ]
    monkeypatch.setattr(am, "resolve", lambda url, **kw: tracks)
    cfg = Config(library_root=tmp_path)
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        app.query_one("#url", Input).value = "https://music.apple.com/us/album/saw/1"
        app.query_one("#url", Input).focus()
        await pilot.press("enter")
        await pilot.pause()
        assert [i.title for i in app.items] == [
            "Aphex Twin — Xtal", "Aphex Twin — Ageispolis"]
        assert all(i.url.startswith("https://music.apple.com") for i in app.items)


@pytest.mark.asyncio
async def test_apple_song_link_enqueues_one_row(tmp_path):
    cfg = Config(library_root=tmp_path)
    app = CrateApp(cfg=cfg, download_fn=lambda *a, **k: None)
    async with app.run_test() as pilot:
        app.query_one("#url", Input).value = (
            "https://music.apple.com/us/album/a/1?i=2")
        app.query_one("#url", Input).focus()
        await pilot.press("enter")
        assert len(app.items) == 1
