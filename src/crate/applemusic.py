"""Apple Music links resolve to *metadata*, never to Apple's own audio.

Apple's catalogue streams are FairPlay-encrypted, so there is nothing here that
touches them. A music.apple.com link is turned into artist/title/duration via
the public iTunes lookup API, and that becomes a search query for the sources
crate already downloads from. Apple's own 30–90s preview clip (an ordinary,
unencrypted m4a served for the web player) is the last-resort fallback when the
track is too obscure to exist anywhere else.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

LOOKUP_URL = "https://itunes.apple.com/lookup"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

# /<storefront>/<kind>/<slug>/<id>  — storefront and slug are both optional in
# the wild (shortened shares drop the slug), so only kind + id are required.
_URL_RE = re.compile(
    r"^https?://(?:geo\.)?music\.apple\.com/(?:([a-z]{2})/)?"
    r"(album|song|music-video)/(?:[^/]+/)?([0-9]+)",
    re.I,
)


class AppleMusicError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppleRef:
    kind: str          # "song" | "album"
    id: str            # album id for albums, track id for songs
    storefront: str    # two-letter country code


@dataclass(frozen=True)
class AppleTrack:
    title: str
    artist: str
    album: str
    duration: float          # seconds
    preview_url: str
    source_url: str


def is_apple_url(url: str) -> bool:
    return "music.apple.com" in url.lower()


def parse_apple_url(url: str) -> AppleRef:
    m = _URL_RE.match(url.strip())
    if not m:
        if "playlist" in url.lower():
            raise AppleMusicError(
                "Apple Music playlists aren't in the public catalogue API — "
                "share the individual song instead")
        raise AppleMusicError("not a recognizable Apple Music song/album link")
    storefront, kind, ident = m.group(1) or "us", m.group(2).lower(), m.group(3)
    # an album link with ?i=<track id> points at one song inside that album
    track_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("i")
    if track_id:
        return AppleRef("song", track_id[0], storefront)
    if kind in ("song", "music-video"):
        return AppleRef("song", ident, storefront)
    return AppleRef("album", ident, storefront)


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _result_to_track(r: dict, source_url: str) -> AppleTrack:
    return AppleTrack(
        title=r.get("trackName") or r.get("collectionName") or "untitled",
        artist=r.get("artistName", "unknown"),
        album=r.get("collectionName", ""),
        duration=float(r.get("trackTimeMillis") or 0) / 1000.0,
        preview_url=r.get("previewUrl", ""),
        source_url=r.get("trackViewUrl") or source_url,
    )


def lookup(ref: AppleRef, url: str, fetch=_fetch_json) -> list[AppleTrack]:
    """Resolve a ref to its tracks. `fetch` is injected in tests."""
    params = {"id": ref.id, "country": ref.storefront}
    if ref.kind == "album":
        params["entity"] = "song"  # returns the collection + each of its songs
    data = fetch(f"{LOOKUP_URL}?{urllib.parse.urlencode(params)}")
    results = data.get("results") or []
    tracks = [
        _result_to_track(r, url)
        for r in results
        if r.get("wrapperType") in ("track", "song") or r.get("kind") == "song"
    ]
    if not tracks:
        raise AppleMusicError(
            f"Apple Music has no track for id {ref.id} in storefront "
            f"'{ref.storefront}' — try the link from your own region")
    return tracks


def resolve(url: str, fetch=_fetch_json) -> list[AppleTrack]:
    return lookup(parse_apple_url(url), url, fetch=fetch)


def search_query(track: AppleTrack) -> str:
    """What to hand a search-capable extractor to find the same recording."""
    return f"{track.artist} {track.title}".strip()
