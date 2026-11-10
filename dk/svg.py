"""SVG primitives shared by every layout. Each text element carries data-box with the id of the box it
must stay inside, so `dk check` can verify the layout in a real browser."""
from __future__ import annotations

from dk.theme import THEME, Theme, esc


class Canvas:
    def __init__(self, theme: Theme = THEME):
        self.t = theme
        self.parts: list[str] = []

    def rect(self, x, y, w, h, fill, stroke="none", sw=1.5, r=None, box_id=None, dash=None):
        r = self.t.radius if r is None else r
        bid = f' data-id="{box_id}"' if box_id else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" '
                          f'stroke="{stroke}" stroke-width="{sw}"{d}{bid}/>')

    def text(self, x, y, s, size, fill, weight=400, mono=False, anchor="start", ls=0.0, box=None):
        fam = self.t.mono if mono else self.t.sans
        b = f' data-box="{box}"' if box else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
                          f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{b}>{esc(s)}</text>')

    def line(self, pts, color, sw=2.5, dash=None, arrow=True):
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#dk-a)"' if arrow else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da}{m} '
                          f'stroke-linejoin="round" stroke-linecap="round"/>')

    def circle(self, x, y, r, fill):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def render(self, w, h, bg, title) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h:.0f}" width="{w}" height="{h:.0f}" '
                f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
                f'<defs><marker id="dk-a" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" '
                f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>'
                f'<rect width="{w}" height="{h:.0f}" rx="28" fill="{bg}" data-id="canvas"/>' + "".join(self.parts) + "</svg>")


def header(c: Canvas, spec: dict) -> float:
    """Kicker + title at the top; returns the y where content can start."""
    t = c.t
    y = 84
    if spec.get("kicker"):
        c.text(t.margin, y, spec["kicker"].upper(), 15, t.accent, 600, mono=True, ls=2, box="canvas")
        y += 44
    c.text(t.margin, y, spec["title"], 34, t.ink, 700, box="canvas")
    y += 20
    if spec.get("subtitle"):
        y += 26
        c.text(t.margin, y, spec["subtitle"], 18, t.body, box="canvas")
    return y + 48
