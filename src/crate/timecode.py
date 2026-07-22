from __future__ import annotations


def parse_timecode(s: str) -> float:
    s = s.strip()
    if not s:
        raise ValueError("empty timecode")
    parts = s.split(":")
    if len(parts) > 3:
        raise ValueError(f"too many segments: {s!r}")
    try:
        nums = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"non-numeric timecode: {s!r}") from exc
    if any(n < 0 for n in nums):
        raise ValueError(f"negative timecode: {s!r}")
    # for multi-part forms, all but the leading segment are 0-59
    for n in nums[1:]:
        if n >= 60:
            raise ValueError(f"segment out of range: {s!r}")
    total = 0.0
    for n in nums:
        total = total * 60 + n
    return total


def format_timecode(seconds: float) -> str:
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def format_slug(seconds: float) -> str:
    seconds = int(round(seconds))
    m, sec = divmod(seconds, 60)
    return f"{m}.{sec:02d}"
