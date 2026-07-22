import pytest
from crate.timecode import parse_timecode, format_timecode, format_slug


@pytest.mark.parametrize("text,secs", [
    ("92", 92.0),
    ("1:32", 92.0),
    ("1:04.5", 64.5),
    ("1:02:03", 3723.0),
    ("0:40", 40.0),
])
def test_parse(text, secs):
    assert parse_timecode(text) == secs


@pytest.mark.parametrize("bad", ["", "abc", "1:2:3:4", "1:99", ":30", "-5"])
def test_parse_rejects_bad(bad):
    with pytest.raises(ValueError):
        parse_timecode(bad)


def test_format_timecode():
    assert format_timecode(92) == "1:32"
    assert format_timecode(3723) == "1:02:03"
    assert format_timecode(40) == "0:40"


def test_format_slug():
    assert format_slug(32) == "0.32"
    assert format_slug(92) == "1.32"
