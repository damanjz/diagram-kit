"""python -m dk render SPEC.yaml [SPEC.yaml ...] [-o OUT_DIR]   render specs to SVG (next to the spec by default)
python -m dk check FILE.svg [...]                                  measure real text boxes in a browser (needs playwright)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path



def render_file(spec_path: Path, out_dir: Path | None) -> Path:
    import yaml

    from dk import flow, trace

    LAYOUTS = {"flow": flow.render, "trace": trace.render}
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    kind = spec.get("type")
    if kind not in LAYOUTS:
        raise SystemExit(f"{spec_path}: type must be one of {sorted(LAYOUTS)}")
    out = (out_dir or spec_path.parent) / (spec_path.stem + ".svg")
    out.write_text(LAYOUTS[kind](spec), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(prog="dk")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("specs", nargs="+", type=Path)
    r.add_argument("-o", "--out", type=Path)
    k = sub.add_parser("check")
    k.add_argument("svgs", nargs="+", type=Path)
    k.add_argument("--png", action="store_true", help="also save a PNG next to each SVG")
    a = ap.parse_args()
    if a.cmd == "render":
        for s in a.specs:
            print("wrote", render_file(s, a.out))
        return 0
    from dk.check import check

    bad = 0
    for s in a.svgs:
        problems = check(s, png=a.png)
        bad += len(problems)
        print(f"{s}: {'ok' if not problems else str(len(problems)) + ' problem(s)'}")
        for p in problems:
            print("  -", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
