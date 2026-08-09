#!/usr/bin/env python3
"""Generate bilingual A3 booklets and A0 boards with Typst."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

TYPST = Path("/opt/homebrew/bin/typst")

COPY = {
    "zh": {
        "title": "Urban Field Dynamics｜城市场演化系统",
        "subtitle": "公共部门不指定唯一终局，而是塑造城市演化条件",
        "quote": "We do not optimise the city. We optimise the conditions under which the city evolves.",
        "scope": "EXPLORATORY POLICY MODEL · PROVISIONAL GEOMETRY · SYNTHETIC SMOKE",
        "method": "方法与证据链",
        "scales": "三层范围、时间尺度与重点区",
        "feedback": "交通—开发—环境反馈",
        "evidence": "当前可复核的机制证据",
        "decisions": "Commitment / Optionality / Trigger",
        "commit": "承诺：无悔骨架与硬保护",
        "option": "选择权：低成本可逆试验",
        "trigger": "触发器：预先声明升级、等待或退出条件",
        "implemented": "已实现：strict contracts、Philox event tapes、transition inertia、P0/P1、8 matched worlds、no-inertia ablation、replay verifier。",
        "missing": "尚未实现或校准：居民/企业完整动力、交通分配、环境场、服务容量、真实 policy search。缺官方 polygon、建筑、权属、OD、容量和历史变化数据。",
        "warning": "当前 2 / 16 / 16 仅为 synthetic mechanism qualification；不得解释为海淀更新概率、地价、客流或审定指标。",
        "board1": "01 · METHOD / INITIAL CONDITIONS",
        "board2": "02 · FEEDBACK / EVIDENCE / ACTION",
    },
    "en": {
        "title": "Urban Field Dynamics",
        "subtitle": "Shape the conditions under which the city evolves, not one prescribed end state",
        "quote": "We do not optimise the city. We optimise the conditions under which the city evolves.",
        "scope": "EXPLORATORY POLICY MODEL · PROVISIONAL GEOMETRY · SYNTHETIC SMOKE",
        "method": "Method and evidence chain",
        "scales": "Scopes, timescales, and key areas",
        "feedback": "Mobility–development–environment feedback",
        "evidence": "Current auditable mechanism evidence",
        "decisions": "Commitment / Optionality / Trigger",
        "commit": "Commitment: no-regret backbone and hard protection",
        "option": "Optionality: low-cost reversible trials",
        "trigger": "Trigger: pre-declared rules to scale, wait, or exit",
        "implemented": "Implemented: strict contracts, Philox event tapes, transition inertia, P0/P1, eight matched worlds, a no-inertia ablation, and full replay verification.",
        "missing": "Not yet implemented or calibrated: complete household/firm dynamics, traffic assignment, environmental fields, service capacity, and real policy search. Official polygons, buildings, ownership, OD, capacity, and historical transitions are missing.",
        "warning": "The current 2 / 16 / 16 result is synthetic mechanism qualification only. It is not a Haidian probability, value, ridership, or statutory metric.",
        "board1": "01 · METHOD / INITIAL CONDITIONS",
        "board2": "02 · FEEDBACK / EVIDENCE / ACTION",
    },
}


def q(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def image_path(figures: Path, name: str, lang: str) -> str:
    suffix = ".en" if lang == "en" else ""
    return q(str((figures / f"{name}{suffix}.png").resolve()))


def common(width: int, height: int, margin: int, body_size: int) -> str:
    return f"""
#set page(width: {width}mm, height: {height}mm, margin: {margin}mm, fill: rgb("#f7f8f5"))
#set text(font: ("Hiragino Sans GB", "Helvetica"), size: {body_size}pt, fill: rgb("#172725"))
#set par(leading: 0.62em)
#let teal = rgb("#167d78")
#let amber = rgb("#c7802b")
#let red = rgb("#b6534c")
#let muted = rgb("#60706c")
"""


def figure_page(title: str, path: str, max_height: str = "245mm") -> str:
    return f"""
#pagebreak()
#text(size: 25pt, weight: "bold")[{q(title)}]
#v(4mm)
#align(center)[#image("{path}", width: 100%, height: {max_height}, fit: "contain")]
"""


def a3_document(lang: str, figures: Path) -> str:
    c = COPY[lang]
    source = common(420, 297, 10, 12)
    source += f"""
#text(size: 9pt, weight: "bold", fill: amber)[{q(c["scope"])}]
#line(length: 100%, stroke: 0.8pt + rgb("#bcc9c4"))
#v(8mm)
#text(size: 39pt, weight: "bold")[{q(c["title"])}]
#v(4mm)
#text(size: 19pt, fill: muted)[{q(c["subtitle"])}]
#v(1fr)
#block(stroke: (left: 3pt + teal), inset: (left: 8mm, y: 4mm))[
  #text(size: 23pt, weight: "bold")[{q(c["quote"])}]
]
#v(1fr)
#text(size: 10pt, fill: muted)[Python 3.12 · 8 matched worlds · 24 smoke runs · engine 524ee2f]
"""
    source += figure_page(c["method"], image_path(figures, "site-overview", lang))
    source += f"""
#pagebreak()
#text(size: 25pt, weight: "bold")[{q(c["scales"])}]
#v(5mm)
#grid(
  columns: (1fr, 1fr),
  gutter: 8mm,
  image("{image_path(figures, "land-use-structure", lang)}", width: 100%),
  image("{image_path(figures, "key-areas", lang)}", width: 100%),
)
#v(4mm)
#text(size: 10pt, fill: muted)[Official geometry and professional controls remain replacement inputs.]
"""
    source += figure_page(c["feedback"], image_path(figures, "mobility-bluegreen", lang))
    source += figure_page(c["evidence"], image_path(figures, "metrics-evidence", lang))
    source += f"""
#pagebreak()
#text(size: 28pt, weight: "bold")[{q(c["decisions"])}]
#v(8mm)
#grid(
  columns: (1fr, 1fr, 1fr), gutter: 8mm,
  block(stroke: (top: 3pt + teal), inset: 5mm)[#text(size: 16pt, weight: "bold")[{q(c["commit"])}]],
  block(stroke: (top: 3pt + amber), inset: 5mm)[#text(size: 16pt, weight: "bold")[{q(c["option"])}]],
  block(stroke: (top: 3pt + red), inset: 5mm)[#text(size: 16pt, weight: "bold")[{q(c["trigger"])}]],
)
#v(12mm)
#text(size: 17pt, weight: "bold")[Implementation boundary]
#v(3mm)
{q(c["implemented"])}
#v(6mm)
#block(fill: rgb("#fff7e8"), stroke: (left: 2pt + amber), inset: 5mm)[{q(c["missing"])}]
#v(6mm)
#block(fill: rgb("#fff1ef"), stroke: (left: 2pt + red), inset: 5mm)[{q(c["warning"])}]
"""
    return source


def a0_document(lang: str, figures: Path) -> str:
    c = COPY[lang]
    source = common(1189, 841, 25, 28)
    source += f"""
#align(right)[#text(size: 18pt, fill: muted)[{q(c["board1"])}]]
#text(size: 78pt, weight: "bold")[{q(c["title"])}]
#text(size: 35pt, fill: muted)[{q(c["subtitle"])}]
#v(12mm)
#line(length: 100%, stroke: 2pt + rgb("#bcc9c4"))
#v(15mm)
#grid(
  columns: (1fr, 1fr), gutter: 24mm,
  [
    #text(size: 38pt, weight: "bold")[{q(c["method"])}]
    #v(8mm)
    #image("{image_path(figures, "site-overview", lang)}", width: 100%)
  ],
  [
    #text(size: 38pt, weight: "bold")[{q(c["scales"])}]
    #v(8mm)
    #image("{image_path(figures, "land-use-structure", lang)}", width: 100%)
    #v(12mm)
    #image("{image_path(figures, "key-areas", lang)}", width: 100%)
  ],
)
#pagebreak()
#align(right)[#text(size: 18pt, fill: muted)[{q(c["board2"])}]]
#text(size: 66pt, weight: "bold")[{q(c["feedback"])}]
#v(12mm)
#line(length: 100%, stroke: 2pt + rgb("#bcc9c4"))
#v(15mm)
#grid(
  columns: (1fr, 1fr), gutter: 24mm,
  [
    #image("{image_path(figures, "mobility-bluegreen", lang)}", width: 100%)
    #v(15mm)
    #block(stroke: (left: 5pt + teal), inset: 10mm)[
      #text(size: 31pt, weight: "bold")[{q(c["commit"])}] #linebreak()
      #text(size: 31pt, weight: "bold")[{q(c["option"])}] #linebreak()
      #text(size: 31pt, weight: "bold")[{q(c["trigger"])}]
    ]
  ],
  [
    #image("{image_path(figures, "metrics-evidence", lang)}", width: 100%)
    #v(15mm)
    #block(fill: rgb("#fff1ef"), stroke: (left: 5pt + red), inset: 10mm)[{q(c["warning"])}]
    #v(12mm)
    {q(c["implemented"])}
    #v(8mm)
    #text(fill: muted)[{q(c["missing"])}]
  ],
)
"""
    return source


def compile_typst(source: str, output: Path) -> None:
    if not TYPST.exists():
        raise RuntimeError(f"Typst not found: {TYPST}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ufd-typst-") as temp:
        source_path = Path(temp) / "document.typ"
        source_path.write_text(source, encoding="utf-8")
        subprocess.run(
            [str(TYPST), "compile", "--root", "/", str(source_path), str(output)],
            check=True,
            timeout=120,
        )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"PDF was not generated: {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--figures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for lang, suffix in (("zh", ""), ("en", ".en")):
        compile_typst(a3_document(lang, args.figures), args.output / f"a3-booklet{suffix}.pdf")
        compile_typst(a0_document(lang, args.figures), args.output / f"a0-boards{suffix}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
