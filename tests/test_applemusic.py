import pytest

from crate.applemusic import (
    AppleMusicError, AppleTrack, is_apple_url, parse_apple_url, resolve,
    search_query,
)
from crate.downloader import apple_meta, pick_search_entry

_SONG = "https://music.apple.com/us/album/better-together/1440857781?i=1440857786"
_ALBUM = "https://music.apple.com/gb/album/in-between-dreams/1440857781"


def _api(results):
    return lambda url: {"resultCount": len(results), "results": results}


def _row(**kw):
    base = {
        "wrapperType": "track", "kind": "song", "trackName": "Xtal",
        "artistName": "Aphex Twin", "collectionName": "SAW 85-92",
        "trackTimeMillis": 294000, "previewUrl": "https://audio/x.m4a",
        "trackViewUrl": "https://music.apple.com/us/album/x/1?i=2",
    }
    base.update(kw)
    return base


def test_is_apple_url():
    assert is_apple_url(_SONG)
    assert not is_apple_url("https://youtube.com/watch?v=abc")


def test_parse_album_link_with_track_query_is_a_song():
    ref = parse_apple_url(_SONG)
    assert (ref.kind, ref.id, ref.storefront) == ("song", "1440857786", "us")


def test_parse_bare_album_link():
    ref = parse_apple_url(_ALBUM)
    assert (ref.kind, ref.id, ref.storefront) == ("album", "1440857781", "gb")


def test_parse_song_link_without_storefront():
    ref = parse_apple_url("https://music.apple.com/song/never-know/1440857794")
    assert (ref.kind, ref.id, ref.storefront) == ("song", "1440857794", "us")


def test_parse_playlist_link_explains_itself():
    with pytest.raises(AppleMusicError, match="playlist"):
        parse_apple_url("https://music.apple.com/us/playlist/mix/pl.u-abc")


def test_parse_rejects_non_apple():
    with pytest.raises(AppleMusicError):
        parse_apple_url("https://youtube.com/watch?v=abc")


def test_resolve_builds_track():
    track = resolve(_SONG, fetch=_api([_row()]))[0]
    assert track.title == "Xtal"
    assert track.artist == "Aphex Twin"
    assert track.duration == 294.0
    assert track.source_url.startswith("https://music.apple.com")


def test_resolve_drops_the_collection_row():
    rows = [{"wrapperType": "collection", "artistName": "Aphex Twin"}, _row()]
    assert len(resolve(_ALBUM, fetch=_api(rows))) == 1


def test_resolve_empty_names_the_storefront():
    with pytest.raises(AppleMusicError, match="storefront 'us'"):
        resolve(_SONG, fetch=_api([]))


def test_search_query_is_artist_then_title():
    track = resolve(_SONG, fetch=_api([_row()]))[0]
    assert search_query(track) == "Aphex Twin Xtal"


def test_pick_search_entry_prefers_matching_runtime():
    entries = [{"id": "a", "duration": 60}, {"id": "b", "duration": 297}]
    assert pick_search_entry(entries, 294.0)["id"] == "b"


def test_pick_search_entry_falls_back_to_top_hit():
    entries = [{"id": "a", "duration": 10}, {"id": "b", "duration": 20}]
    assert pick_search_entry(entries, 294.0)["id"] == "a"


def test_pick_search_entry_without_a_target():
    assert pick_search_entry([{"id": "a"}], 0.0)["id"] == "a"


def test_pick_search_entry_empty():
    assert pick_search_entry([], 294.0) is None


def test_apple_meta_labels_previews():
    track = AppleTrack("Xtal", "Aphex Twin", "SAW", 294.0, "http://p", "http://s")
    assert apple_meta(track, "sample", "m4a", preview=False).title == "Xtal"
    full = apple_meta(track, "sample", "m4a", preview=True)
    assert full.title == "Xtal (preview)"
    assert full.uploader == "Aphex Twin"
