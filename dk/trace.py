"""Request trace: lanes across the top, one arrow per step down the page. Labels wrap so they never run past
the canvas; the step grows to fit its label."""
from __future__ import annotations

from dk.svg import Canvas, header
from dk.theme import THEME, text_width, wrap

LABEL, LH, STEP_GAP = 16, 22, 26


def render(spec: dict) -> str:
    t = THEME
    c = Canvas()
    y0 = header(c, spec)
    lanes = spec["lanes"]
    n = len(lanes)
    gutter = 44  # room for step numbers
    span = (t.width - 2 * t.margin - gutter) / n
    xs = {ln["id"]: t.margin + gutter + span * (i + 0.5) for i, ln in enumerate(lanes)}
    head_w = min(220, span - 20)
    for ln in lanes:
        x = xs[ln["id"]]
        hot = ln.get("hot")
        c.rect(x - head_w / 2, y0, head_w, 56, t.accent if hot else t.ink, r=14, box_id=f"lane-{ln['id']}")
        size = 18 if text_width(ln["label"], 18, bold=True) < head_w - 24 else 15
        c.text(x, y0 + 35, ln["label"], size, t.ink if hot else t.paper, 650, anchor="middle", box=f"lane-{ln['id']}")
    y = y0 + 56 + 44
    rows = []
    for n_step, s in enumerate(spec["steps"], 1):
        a, b = xs[s["from"]], xs[s["to"]]
        tone = s.get("tone", "normal")
        color = {"normal": t.ink, "accent": t.accent, "muted": t.soft}[tone]
        tc = {"normal": t.ink, "accent": t.ink, "muted": t.body}[tone]
        weight = 650 if tone == "accent" else 500
        left = min(a, b) + 14
        max_w = max(t.width - t.margin - left - 10, 200)
        lines = wrap(s["text"], LABEL, max_w, bold=weight > 600)
        for i, ln in enumerate(lines):
            c.text(left, y + i * LH, ln, LABEL, tc, weight, box="canvas")
        ay = y + (len(lines) - 1) * LH + 16
        c.circle(t.margin + 12, ay, 12, t.ink if tone != 'accent' else t.accent)
        c.text(t.margin + 12, ay + 4.5, str(n_step), 12, t.paper if tone != 'accent' else t.ink, 700, anchor='middle')
        d = 1 if b > a else -1
        c.line([(a + 6 * d, ay), (b - 6 * d, ay)], color, sw=2.5, dash="6 6" if s.get("dashed") else None)
        rows.append(ay)
        y = ay + STEP_GAP + LH
    end = y + 10
    for ln in lanes:
        x = xs[ln["id"]]
        c.parts.insert(0, f'<line x1="{x:.1f}" y1="{y0 + 56:.1f}" x2="{x:.1f}" y2="{end:.1f}" stroke="{t.line}" '
                          f'stroke-width="2" stroke-dasharray="3 8"/>')
    if spec.get("note"):
        end += 30
        c.text(t.margin, end, spec["note"], 16, t.soft, box="canvas")
    # lifelines go under everything: move the background-free parts after the header text is fine visually
    return c.render(t.width, end + t.margin - 20, t.paper, spec["title"])
