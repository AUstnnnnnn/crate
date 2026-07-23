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
