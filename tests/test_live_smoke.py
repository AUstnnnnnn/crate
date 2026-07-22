import os
import pytest
from pathlib import Path
from crate.config import Config
from crate.downloader import Downloader

pytestmark = pytest.mark.skipif(
    os.environ.get("CRATE_LIVE_TEST") != "1",
    reason="live network test; set CRATE_LIVE_TEST=1 to run",
)


def test_real_sample_download(tmp_path):
    cfg = Config(library_root=tmp_path, sample_format="wav")
    url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"  # Big Buck Bunny trailer
    path, meta = Downloader().download(url, cfg, "sample", lambda d: None)
    assert Path(path).exists()
    assert meta.title
