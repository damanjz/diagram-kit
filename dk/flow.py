"""Flow map: columns left to right (cards, an accent core group, or a vertical stack), arrows between them,
and an optional data band along the bottom. Text wraps to the column width; heights follow content."""
from __future__ import annotations

from dataclasses import dataclass, field

from dk.svg import Canvas, header
from dk.theme import THEME, text_width, wrap

TAG, TITLE, BODY, LH = 13, 22, 16, 24
STACK_GAP = 34


@dataclass
class Box:
    id: str
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    draw: object = None
    kids: list = field(default_factory=list)


def _card_height(card: dict, w: float, title_size=TITLE) -> tuple[float, list[str]]:
    t = THEME
    inner = w - 2 * t.pad
    lines: list[str] = []
    for p in card.get("points", []):
        lines += wrap(p, BODY, inner)
    title_lines = wrap(card.get("title", ""), title_size, inner, bold=True)
    h = t.pad + (30 if card.get("tag") else 0) + len(title_lines) * (title_size + 8) + 8 + len(lines) * LH + t.pad
    return h, lines


def _draw_card(c: Canvas, b: Box, card: dict, style: str = "light", title_size=TITLE, lines=None):
    t = THEME
    fill, tc, sc, stroke = {
        "light": (t.card, t.ink, t.body, t.line),
        "dark": (t.ink, t.paper, t.dark_body, "none"),
        "accent": (t.accent, t.ink, t.ink, "none"),
        "plain": (t.card, t.ink, t.body, "none"),
    }[style]
    c.rect(b.x, b.y, b.w, b.h, fill, stroke, box_id=b.id)
    y = b.y + t.pad
    if card.get("tag"):
        c.text(b.x + t.pad, y + 14, card["tag"].upper(), TAG, t.accent if style != "accent" else t.ink, 600,
               mono=True, ls=1.5, box=b.id)
        y += 30
    for tl in wrap(card.get("title", ""), title_size, b.w - 2 * t.pad, bold=True):
        c.text(b.x + t.pad, y + title_size, tl, title_size, tc, 650, box=b.id)
        y += title_size + 8
    y += 8
    for ln in lines if lines is not None else []:
        c.text(b.x + t.pad, y + BODY + 2, ln, BODY, sc, box=b.id)
        y += LH


def render(spec: dict) -> str:
    t = THEME
    c = Canvas()
    y0 = header(c, spec)
    cols = spec["columns"]
    weights = [col.get("grow", 1.7 if "core" in col else 1.0) for col in cols]
    avail = t.width - 2 * t.margin - t.gap * (len(cols) - 1)
    widths = [avail * w / sum(weights) for w in weights]
    nodes: dict[str, Box] = {}
    x = t.margin
    plans = []
    # 1) measure
    single_h = 0.0
    for col, w in zip(cols, widths):
        if "core" in col:
            core = col["core"]
            kid_w = w - 2 * t.pad
            kids = []
            for k in core.get("children", []):
                h, lines = _card_height(k, kid_w)
                kids.append((k, h, lines))
            head = t.pad + 30 + 34 + (26 if core.get("subtitle") else 0) + 14
            h = head + sum(kh for _, kh, _ in kids) + 18 * (len(kids) - 1) + t.pad
            plans.append(("core", col, w, h, kids, head))
        elif "stack" in col:
            items = []
            for k in col["stack"]:
                h, lines = _card_height(k, w)
                items.append((k, h, lines))
            plans.append(("stack", col, w, None, items, 0))
        else:
            h, lines = _card_height(col, w)
            single_h = max(single_h, h)
            plans.append(("card", col, w, h, lines, 0))
    # 2) place: every column is centred on the tallest one
    def col_h(plan):
        kind, col, w, h, extra, head = plan
        if kind == 'card':
            return single_h
        if kind == 'stack':
            return sum(kh for _, kh, _ in extra) + STACK_GAP * (len(extra) - 1)
        return h
    row_h = max(col_h(pl) for pl in plans)
    bottom = y0 + row_h
    for kind, col, w, h, extra, head in plans:
        if kind == "card":
            b = Box(col["id"], x, y0 + (row_h - single_h) / 2, w, single_h)
            _draw_card(c, b, col, col.get("style", "light"), lines=extra)
            nodes[b.id] = b
        elif kind == "stack":
            y = y0 + (row_h - col_h((kind, col, w, h, extra, head))) / 2
            for k, kh, lines in extra:
                b = Box(k["id"], x, y, w, kh)
                _draw_card(c, b, k, k.get("style", "light"), lines=lines)
                nodes[b.id] = b
                y += b.h + STACK_GAP
        else:
            core = col["core"]
            b = Box(col["id"], x, y0 + (row_h - h) / 2, w, h)
            c.rect(b.x, b.y, b.w, b.h, t.accent, box_id=b.id)
            c.text(b.x + t.pad, b.y + t.pad + 14, core.get("tag", "").upper(), TAG, t.ink, 600, mono=True, ls=1.5, box=b.id)
            c.text(b.x + t.pad, b.y + t.pad + 30 + 26, core["title"], 26, t.ink, 700, box=b.id)
            if core.get("subtitle"):
                c.text(b.x + t.pad, b.y + t.pad + 30 + 26 + 28, core["subtitle"], 16, t.ink, box=b.id)
            nodes[b.id] = b
            ky = b.y + head
            for k, kh, lines in extra:
                kb = Box(k["id"], b.x + t.pad, ky, w - 2 * t.pad, kh)
                _draw_card(c, kb, k, k.get("style", "plain"), lines=lines)
                nodes[kb.id] = kb
                ky += kh + 18
        x += w + t.gap
    # 3) band
    y = bottom + 50
    band = spec.get("band")
    if band:
        bb = Box("band", t.margin, y, t.width - 2 * t.margin, 76)
        c.rect(bb.x, bb.y, bb.w, bb.h, t.band, box_id="band")
        c.text(bb.x + 24, bb.y + 46, band["title"], 20, t.ink, 650, box="band")
        if band.get("text"):
            tx = bb.x + 24 + text_width(band["title"], 20, bold=True) + 32
            c.text(tx, bb.y + 46, band["text"], 17, t.body, box="band")
        if band.get("right"):
            c.text(bb.x + bb.w - 24, bb.y + 46, band["right"], 20, t.ink, 700, anchor="end", box="band")
        nodes["band"] = bb
        y += 76
    # 4) edges
    for e in spec.get("edges", []):
        a, b = nodes[e["from"]], nodes[e["to"]]
        dash = "7 7" if e.get("dashed") else None
        if b.x >= a.x + a.w - 1:  # target to the right
            top, bot = max(a.y, b.y), min(a.y + a.h, b.y + b.h)
            yy = (top + bot) / 2 if bot > top else (a.y + a.h / 2)
            c.line([(a.x + a.w + 4, yy), (b.x - 6, yy)], t.ink, dash=dash)
        elif b.y >= a.y + a.h - 1:  # target below
            left, right = max(a.x, b.x), min(a.x + a.w, b.x + b.w)
            xx = (left + right) / 2 if right > left else a.x + a.w / 2
            c.line([(xx, a.y + a.h + 4), (xx, b.y - 6)], t.ink, dash=dash)
        else:  # target to the left (a return path), drawn under the row
            yy = max(a.y + a.h, b.y + b.h) + 24
            c.line([(a.x + a.w / 2, a.y + a.h + 4), (a.x + a.w / 2, yy), (b.x + b.w / 2, yy), (b.x + b.w / 2, b.y + b.h + 6)],
                   t.accent, dash=dash)
    if spec.get("note"):
        y += 40
        c.text(t.margin, y, spec["note"], 16, t.soft, box="canvas")
    return c.render(t.width, y + t.margin, t.paper, spec["title"])
