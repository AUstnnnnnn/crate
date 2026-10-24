import pytest

import crate.state as state


@pytest.fixture(autouse=True)
def isolate_state(tmp_path, monkeypatch):
    """Keep tests off the real ~/.config/crate/state.json (read *and* write)."""
    monkeypatch.setattr(state, "STATE_PATH", tmp_path / "state.json")
