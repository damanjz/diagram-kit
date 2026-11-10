"""Brand tokens and text measuring. Change the look here; every diagram follows."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    ink: str = "#141414"
    paper: str = "#e9e9e7"
    accent: str = "#fe6608"
    soft: str = "#8c8a85"
    body: str = "#55534f"
    card: str = "#ffffff"
    line: str = "#d2d0cb"
    band: str = "#dcdad5"
    dark_body: str = "#c9c7c2"
    sans: str = "Segoe UI, Inter, -apple-system, Helvetica, Arial, sans-serif"
    mono: str = "Cascadia Mono, SFMono-Regular, Consolas, ui-monospace, monospace"
    width: int = 1600
    margin: int = 64
    gap: int = 56          # between flow columns (room for an arrow)
    radius: int = 16
    pad: int = 22          # inside a card


THEME = Theme()

# Average glyph advance as a share of font size. Deliberately generous so text measured here is never
# narrower than it renders; `python -m dk check` measures the real layout in a browser.
_SANS_ADV = {"bold": 0.60, "normal": 0.54}
_MONO_ADV = 0.62
_NARROW = set("iljtfr.,:;'!|() []")
_WIDE = set("mwMW@%")


def text_width(s: str, size: float, mono: bool = False, bold: bool = False) -> float:
    if mono:
        return len(s) * size * _MONO_ADV
    base = _SANS_ADV["bold" if bold else "normal"]
    w = 0.0
    for ch in s:
        if ch in _NARROW:
            w += base * 0.55
        elif ch in _WIDE:
            w += base * 1.45
        elif ch.isupper():
            w += base * 1.18
        else:
            w += base
    return w * size


def wrap(s: str, size: float, max_w: float, mono: bool = False, bold: bool = False) -> list[str]:
    """Greedy word wrap by measured width."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and text_width(trial, size, mono, bold) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
