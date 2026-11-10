"""Measure the rendered layout in Chromium: every text must sit inside the box it belongs to (with padding),
nothing may leave the canvas, and boxes at the same level must not overlap. Rules are checked, not eyeballed."""
from __future__ import annotations

import os
from pathlib import Path

JS = """
() => {
  const svg = document.querySelector('svg');
  const boxes = {};
  for (const r of svg.querySelectorAll('[data-id]')) {
    const b = r.getBBox(); boxes[r.dataset.id] = {x: b.x, y: b.y, w: b.width, h: b.height, tag: r.tagName};
  }
  const texts = [];
  for (const t of svg.querySelectorAll('text[data-box]')) {
    const b = t.getBBox(); texts.push({box: t.dataset.box, s: t.textContent, x: b.x, y: b.y, w: b.width, h: b.height});
  }
  return {boxes, texts};
}
"""
PAD = 8  # text must keep at least this much space from its box edge (canvas: from the rounded frame)


def check(svg_path: Path, png: bool = False) -> list[str]:
    from playwright.sync_api import sync_playwright

    exe = os.environ.get("DK_CHROME")
    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page()
        page.goto(Path(svg_path).resolve().as_uri())
        data = page.evaluate(JS)
        if png:
            page.locator("svg").screenshot(path=str(Path(svg_path).with_suffix(".png")))
        browser.close()
    boxes, texts = data["boxes"], data["texts"]
    for tx in texts:
        b = boxes.get(tx["box"])
        if not b:
            problems.append(f"text {tx['s']!r} names unknown box {tx['box']}")
            continue
        pad = 24 if tx["box"] == "canvas" else PAD
        if (tx["x"] < b["x"] + pad - 0.5 or tx["x"] + tx["w"] > b["x"] + b["w"] - pad + 0.5
                or tx["y"] < b["y"] + 2 or tx["y"] + tx["h"] > b["y"] + b["h"] - 2):
            over = tx["x"] + tx["w"] - (b["x"] + b["w"] - pad)
            problems.append(f"text {tx['s'][:50]!r} leaves box {tx['box']} (right overflow {over:.0f}px)")
    rects = [(k, v) for k, v in boxes.items() if k != "canvas"]
    for i, (ka, a) in enumerate(rects):
        for kb, b in rects[i + 1:]:
            inside = (b["x"] >= a["x"] and b["x"] + b["w"] <= a["x"] + a["w"] and b["y"] >= a["y"]
                      and b["y"] + b["h"] <= a["y"] + a["h"]) or (
                      a["x"] >= b["x"] and a["x"] + a["w"] <= b["x"] + b["w"] and a["y"] >= b["y"]
                      and a["y"] + a["h"] <= b["y"] + b["h"])
            ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if ox > 0 and oy > 0 and not inside:
                problems.append(f"boxes {ka} and {kb} overlap")
    c = boxes.get("canvas")
    for k, v in rects:
        if c and (v["x"] < 0 or v["y"] < 0 or v["x"] + v["w"] > c["w"] or v["y"] + v["h"] > c["h"]):
            problems.append(f"box {k} leaves the canvas")
    return problems
