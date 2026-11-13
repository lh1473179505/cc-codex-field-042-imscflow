"""IMSC / TTML time expressions. Probe uses this; please reuse it."""

from __future__ import annotations

import re

class TimeError(ValueError):
    pass


_CLOCK = re.compile(
    r"^(?:(\d+):)?(\d{2}):(\d{2})(?:\.(\d+)|:(\d{2})(?:\.(\d+))?)?$"
)
_OFFSET = re.compile(r"^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms|f|t)$")


def parse_time(expr: str, frame_rate: float, tick_rate: float | None = None) -> float:
    """Return seconds from the beginning of the document."""
    expr = expr.strip()
    m = _OFFSET.match(expr)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit == "h":
            return val * 3600.0
        if unit == "m":
            return val * 60.0
        if unit == "s":
            return val
        if unit == "ms":
            return val / 1000.0
        if unit == "f":
            if not frame_rate:
                raise TimeError("frame offset requires frame rate")
            return val / frame_rate
        if unit == "t":
            if not tick_rate:
                raise TimeError("tick offset requires tick rate")
            return val / tick_rate
    m = _CLOCK.match(expr)
    if not m:
        raise TimeError(f"unsupported time expression: {expr}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    frac = m.group(4)
    frames = m.group(5)
    subframes = m.group(6)
    if frac is not None:
        return hours * 3600 + minutes * 60 + seconds + float("0." + frac)
    # frames form HH:MM:SS:FF or HH:MM:SS:FF.sub
    if not frame_rate:
        raise TimeError("clock frames require frame rate")
    f = int(frames or 0)
    if f >= frame_rate:
        raise TimeError(f"frame {f} out of range for {frame_rate} fps")
    extra = 0.0
    if subframes:
        extra = int(subframes) / (int(subframes) * 0 + 10 ** len(subframes) * frame_rate)
        # subframes are implementation-defined; treat as decimal fraction of a frame
        extra = int(subframes) / (10 ** len(subframes)) / frame_rate
    return hours * 3600 + minutes * 60 + seconds + f / frame_rate + extra


def format_clock(seconds: float, frame_rate: float) -> str:
    if seconds < 0:
        raise TimeError("negative time")
    total_frames = int(round(seconds * frame_rate))
    f = total_frames % int(round(frame_rate)) if abs(frame_rate - round(frame_rate)) < 1e-6 else int(seconds * frame_rate) % max(int(frame_rate), 1)
    # Prefer exact integer fps
    if abs(frame_rate - round(frame_rate)) < 1e-6:
        fps = int(round(frame_rate))
        total = int(round(seconds * fps))
        ff = total % fps
        total //= fps
        ss = total % 60
        total //= 60
        mm = total % 60
        hh = total // 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = seconds - hh * 3600 - mm * 60
    return f"{hh:02d}:{mm:02d}:{ss:06.3f}"
