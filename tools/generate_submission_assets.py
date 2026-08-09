#!/usr/bin/env python3
"""Generate deterministic bilingual submission figures from frozen evidence."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1600
HEIGHT = 900
BG = "#F7F8F5"
INK = "#1D2928"
MUTED = "#5D6D69"
TEAL = "#167D78"
BLUE = "#3A6EA5"
AMBER = "#C7802B"
RED = "#B6534C"
GREEN = "#5A8E62"
LINE = "#BCC9C4"
PALE = "#E9EFEC"

CJK_FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
LATIN_FONT = Path("/System/Library/Fonts/Helvetica.ttc")


def font(size: int, *, bold: bool = False, lang: str = "en") -> ImageFont.FreeTypeFont:
    path = CJK_FONT if lang == "zh" and CJK_FONT.exists() else LATIN_FONT
    index = 1 if bold and path.suffix == ".ttc" else 0
    return ImageFont.truetype(str(path), size=size, index=index)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    return image, ImageDraw.Draw(image)


def text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int,
    *,
    lang: str,
    fill: str = INK,
    bold: bool = False,
    anchor: str = "la",
) -> None:
    draw.text(xy, value, font=font(size, bold=bold, lang=lang), fill=fill, anchor=anchor)


def header(draw: ImageDraw.ImageDraw, title: str, subtitle: str, *, lang: str) -> None:
    text(draw, (90, 72), title, 48, lang=lang, bold=True)
    text(draw, (90, 132), subtitle, 24, lang=lang, fill=MUTED)
    draw.line((90, 172, 1510, 172), fill=LINE, width=3)


def footer(draw: ImageDraw.ImageDraw, note: str, *, lang: str) -> None:
    draw.line((90, 824, 1510, 824), fill=LINE, width=2)
    text(draw, (90, 850), note, 19, lang=lang, fill=MUTED, anchor="lm")


def box(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    *,
    fill: str = "#FFFFFF",
    outline: str = LINE,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(bounds, radius=14, fill=fill, outline=outline, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: str = TEAL,
    width: int = 5,
) -> None:
    draw.line((*start, *end), fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 15
    spread = 0.55
    points = [
        end,
        (
            int(end[0] - length * math.cos(angle - spread)),
            int(end[1] - length * math.sin(angle - spread)),
        ),
        (
            int(end[0] - length * math.cos(angle + spread)),
            int(end[1] - length * math.sin(angle + spread)),
        ),
    ]
    draw.polygon(points, fill=fill)


def multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    *,
    lang: str,
    size: int = 22,
    fill: str = INK,
    gap: int = 10,
    bold_first: bool = False,
) -> None:
    y = xy[1]
    for index, line in enumerate(lines):
        text(draw, (xy[0], y), line, size, lang=lang, fill=fill, bold=bold_first and index == 0)
        y += size + gap


def site_overview(lang: str) -> Image.Image:
    image, draw = canvas()
    labels = {
        "zh": (
            "证据链：资料不会被模型自动升级",
            "从来源等级到可复核策略；每一步保留缺口与人工门",
            ["官方公告 / 任务书", "Provisional polygons", "缺失控规、权属、OD"],
            ["输入证据等级", "可重放 Python engine", "Policy × World × Ablation"],
            ["Commitment", "Optionality", "Trigger"],
            "当前 smoke 仅为 synthetic redevelopment 机制资格化，不是海淀预测。",
        ),
        "en": (
            "Evidence chain: models cannot upgrade source authority",
            "From evidence status to reviewable strategy, retaining gaps and human gates",
            [
                "Official brief / taskbook",
                "Provisional polygons",
                "Missing controls, ownership, OD",
            ],
            ["Input evidence status", "Replayable Python engine", "Policy × World × Ablation"],
            ["Commitment", "Optionality", "Trigger"],
            "Current smoke is synthetic redevelopment qualification, not a Haidian forecast.",
        ),
    }[lang]
    header(draw, labels[0], labels[1], lang=lang)
    columns = [(90, 230, 480, 720), (605, 230, 995, 720), (1120, 230, 1510, 720)]
    titles = [
        "01  SOURCES" if lang == "en" else "01  来源",
        "02  MODEL" if lang == "en" else "02  模型",
        "03  DECISIONS" if lang == "en" else "03  决策",
    ]
    colors = [BLUE, TEAL, AMBER]
    groups = [labels[2], labels[3], labels[4]]
    for bounds, title_value, color, items in zip(columns, titles, colors, groups, strict=True):
        box(draw, bounds)
        text(
            draw,
            (bounds[0] + 28, bounds[1] + 42),
            title_value,
            21,
            lang=lang,
            fill=color,
            bold=True,
        )
        draw.line(
            (bounds[0] + 28, bounds[1] + 72, bounds[2] - 28, bounds[1] + 72), fill=color, width=3
        )
        multiline(draw, (bounds[0] + 28, bounds[1] + 125), items, lang=lang, size=24, gap=34)
    arrow(draw, (500, 475), (580, 475))
    arrow(draw, (1015, 475), (1095, 475))
    text(draw, (540, 435), "status", 18, lang="en", fill=MUTED, anchor="mm")
    text(draw, (1055, 435), "distribution", 18, lang="en", fill=MUTED, anchor="mm")
    footer(draw, labels[5], lang=lang)
    return image


def scope_structure(lang: str) -> Image.Image:
    image, draw = canvas()
    zh = lang == "zh"
    header(
        draw,
        "三层范围 × 四个时间尺度" if zh else "Three scopes × four timescales",
        "战略、城市设计与重点区共享状态合同，但不共享伪精度"
        if zh
        else "Shared state contract without shared false precision",
        lang=lang,
    )
    scope_labels = [
        ("统筹研究范围", "产业网络 · 跨区通勤 · 公共投资")
        if zh
        else ("Coordinated research", "Industry · commuting · public investment"),
        ("总体设计范围", "用地 · 建筑 · 交通 · 环境 · 服务")
        if zh
        else ("Overall design", "Land · buildings · mobility · environment · services"),
        ("三处重点区域", "不同初始条件 · 概念详细设计")
        if zh
        else ("Three key areas", "Contrasting initial conditions · concept detail"),
    ]
    for idx, (title_value, body) in enumerate(scope_labels):
        y = 225 + idx * 150
        draw.rectangle((90, y, 555, y + 112), fill="#FFFFFF", outline=LINE, width=2)
        draw.rectangle((90, y, 105, y + 112), fill=[BLUE, TEAL, AMBER][idx])
        text(draw, (135, y + 32), title_value, 26, lang=lang, bold=True)
        text(draw, (135, y + 76), body, 20, lang=lang, fill=MUTED)
    times = [
        ("HOUR / DAY", "traffic · exposure") if not zh else ("小时 / 日", "交通 · 暴露"),
        ("SEASON", "weather · activity") if not zh else ("季节", "气象 · 活动"),
        ("YEAR", "relocation · firms") if not zh else ("年度", "迁居 · 企业"),
        ("5–30 YEARS", "redevelopment · infrastructure")
        if not zh
        else ("5—30 年", "重建 · 基础设施"),
    ]
    x_positions = [700, 915, 1130, 1345]
    for idx, ((title_value, body), x) in enumerate(zip(times, x_positions, strict=True)):
        draw.ellipse(
            (x - 78, 315 - 78, x + 78, 315 + 78),
            fill="#FFFFFF",
            outline=[BLUE, TEAL, AMBER, RED][idx],
            width=5,
        )
        text(draw, (x, 298), title_value, 20, lang=lang, bold=True, anchor="mm")
        text(draw, (x, 340), body, 17, lang=lang, fill=MUTED, anchor="mm")
        if idx < 3:
            arrow(draw, (x + 88, 315), (x_positions[idx + 1] - 88, 315), fill=LINE, width=3)
    draw.line((680, 490, 1435, 490), fill=LINE, width=2)
    decision = [("COMMITMENT", GREEN), ("OPTIONALITY", BLUE), ("TRIGGER", AMBER)]
    if zh:
        decision = [("承诺", GREEN), ("选择权", BLUE), ("触发器", AMBER)]
    for idx, (label, color) in enumerate(decision):
        x = 720 + idx * 260
        text(draw, (x, 565), label, 24, lang=lang, fill=color, bold=True)
        draw.line((x, 600, x + 190, 600), fill=color, width=5)
    footer(
        draw,
        "Observer 读取涌现形态；形态不进入 objective。"
        if zh
        else "Observers read emergent morphology; morphology is not an objective.",
        lang=lang,
    )
    return image


def key_areas(lang: str) -> Image.Image:
    image, draw = canvas()
    zh = lang == "zh"
    header(
        draw,
        "三处重点区：初始条件、动作与触发器"
        if zh
        else "Three key areas: conditions, actions, triggers",
        "不预埋三中心结果；让机制证明协同是否成立"
        if zh
        else "Do not pre-load three centres; require mechanisms to support coordination",
        lang=lang,
    )
    panels = [
        (
            "众智园",
            "Zhongzhiyuan",
            BLUE,
            ["自主创新 / 测试验证", "可撤回测试路段", "企业 + 容量 + 暴露 trigger"],
        ),
        (
            "AI 原点社区",
            "AI Origin Community",
            TEAL,
            ["知识 / 生活 / 公共服务", "近校步行与安静内部", "服务 + 更新周期 trigger"],
        ),
        (
            "大钟寺",
            "Dazhongsi",
            AMBER,
            ["轨道 / 展示 / 企业服务", "四象限步行与光预算", "交通 + 夜间外部性 trigger"],
        ),
    ]
    if not zh:
        panels = [
            (
                "Zhongzhiyuan",
                "Autonomous innovation",
                BLUE,
                [
                    "Testing and validation",
                    "Reversible test streets",
                    "Firm + capacity + exposure trigger",
                ],
            ),
            (
                "AI Origin Community",
                "Knowledge–life coupling",
                TEAL,
                [
                    "Near-campus walking",
                    "Quiet interior and services",
                    "Capacity + renewal-cycle trigger",
                ],
            ),
            (
                "Dazhongsi",
                "Rail–service coupling",
                AMBER,
                ["Four-quadrant walking", "Night Light Budget", "Mobility + externality trigger"],
            ),
        ]
    for idx, panel in enumerate(panels):
        x0 = 90 + idx * 485
        x1 = x0 + 420
        box(draw, (x0, 230, x1, 720))
        draw.rectangle((x0, 230, x1, 245), fill=panel[2])
        text(draw, (x0 + 28, 292), panel[0], 31, lang=lang, bold=True)
        text(draw, (x0 + 28, 334), panel[1], 20, lang=lang, fill=MUTED)
        multiline(draw, (x0 + 28, 420), panel[3], lang=lang, size=22, gap=28)
        text(draw, (x0 + 28, 674), "PROVISIONAL CONCEPT", 17, lang="en", fill=panel[2], bold=True)
    footer(
        draw,
        "Official polygons、现状建筑、权属和专项条件到位后必须重算。"
        if zh
        else (
            "Recalculate after official polygons, buildings, ownership, "
            "and specialist controls arrive."
        ),
        lang=lang,
    )
    return image


def mobility_bluegreen(lang: str) -> Image.Image:
    image, draw = canvas()
    zh = lang == "zh"
    header(
        draw,
        "交通—开发—环境反馈" if zh else "Mobility–development–environment feedback",
        "公共投资改变条件，但容量、暴露与公平形成硬门"
        if zh
        else "Public investment changes conditions; capacity, exposure, and equity remain gates",
        lang=lang,
    )
    nodes = [
        ((230, 310), "用地" if zh else "Land use", BLUE),
        ((510, 245), "出行" if zh else "Trips", TEAL),
        ((810, 245), "拥堵 / skim" if zh else "Congestion / skim", AMBER),
        ((1110, 310), "可达性" if zh else "Accessibility", BLUE),
        ((1050, 590), "地价 / 收益" if zh else "Value / return", TEAL),
        ((670, 650), "开发闸门" if zh else "Development gate", RED),
        ((310, 590), "用途转换" if zh else "Use transition", AMBER),
    ]
    for (x, y), label, color in nodes:
        draw.ellipse((x - 105, y - 50, x + 105, y + 50), fill="#FFFFFF", outline=color, width=4)
        text(draw, (x, y), label, 22, lang=lang, bold=True, anchor="mm")
    loop_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0)]
    for a, b in loop_edges:
        start = nodes[a][0]
        end = nodes[b][0]
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(math.hypot(dx, dy), 1)
        start2 = (int(start[0] + dx / length * 112), int(start[1] + dy / length * 58))
        end2 = (int(end[0] - dx / length * 112), int(end[1] - dy / length * 58))
        arrow(draw, start2, end2, fill=LINE, width=4)
    gate_labels = [
        ("服务容量" if zh else "Service capacity", 1320, 390),
        ("空气 / 噪声 / 热 / 光" if zh else "Air / noise / heat / light", 1320, 475),
        ("群体负担" if zh else "Distributional burden", 1320, 560),
    ]
    for label, _x, y in gate_labels:
        draw.line((1210, y, 1250, y), fill=RED, width=5)
        text(draw, (1270, y), label, 20, lang=lang, fill=RED, bold=True, anchor="lm")
    footer(
        draw,
        (
            "AequilibraE 仅用于有 OD / capacity 的 selected-scenario oracle；"
            "当前 smoke 未包含交通分配。"
        )
        if zh
        else (
            "AequilibraE is a selected-scenario oracle after OD/capacity data; "
            "current smoke has no assignment."
        ),
        lang=lang,
    )
    return image


def metrics_evidence(lang: str, summary: dict) -> Image.Image:
    image, draw = canvas()
    zh = lang == "zh"
    header(
        draw,
        "Smoke-v1：matched worlds 与 inertia ablation"
        if zh
        else "Smoke-v1: matched worlds and inertia ablation",
        "三 synthetic 单元 × 8 world IDs；纵轴为五年内更新总次数"
        if zh
        else "Three synthetic units × 8 world IDs; y-axis is total redevelopments over five years",
        lang=lang,
    )
    arms = [
        ("P0", summary["arms"]["p0"]["total_redevelopments"], BLUE),
        ("P1", summary["arms"]["p1"]["total_redevelopments"], TEAL),
        ("P0 no inertia", summary["arms"]["p0-no-inertia"]["total_redevelopments"], AMBER),
    ]
    x0, y0, chart_w, chart_h = 150, 720, 850, 450
    draw.line((x0, y0 - chart_h, x0, y0), fill=INK, width=3)
    draw.line((x0, y0, x0 + chart_w, y0), fill=INK, width=3)
    max_value = 20
    for tick in range(0, max_value + 1, 4):
        y = y0 - int(chart_h * tick / max_value)
        draw.line((x0 - 8, y, x0, y), fill=INK, width=2)
        text(draw, (x0 - 18, y), str(tick), 18, lang="en", fill=MUTED, anchor="rm")
    bar_w = 150
    for idx, (label, value, color) in enumerate(arms):
        x = x0 + 115 + idx * 250
        h = int(chart_h * value / max_value)
        draw.rectangle((x, y0 - h, x + bar_w, y0), fill=color)
        text(
            draw,
            (x + bar_w // 2, y0 - h - 28),
            str(value),
            30,
            lang="en",
            fill=color,
            bold=True,
            anchor="mm",
        )
        text(draw, (x + bar_w // 2, y0 + 34), label, 20, lang="en", fill=INK, anchor="mm")
    box(draw, (1090, 280, 1510, 700), fill="#FFFFFF")
    text(
        draw,
        (1120, 330),
        "WHAT THIS SUPPORTS" if not zh else "可支持的结论",
        21,
        lang=lang,
        fill=TEAL,
        bold=True,
    )
    supported = [
        "Same event tapes" if not zh else "相同 event tapes",
        "Policy path is active" if not zh else "政策路径有效",
        "Inertia changes outcome" if not zh else "惯性改变结果",
        "Hard pin: 0 conversions" if not zh else "Hard pin：0 次转换",
    ]
    multiline(draw, (1120, 385), supported, lang=lang, size=21, gap=20)
    text(
        draw,
        (1120, 590),
        "DOES NOT SUPPORT" if not zh else "不支持的推断",
        21,
        lang=lang,
        fill=RED,
        bold=True,
    )
    multiline(
        draw,
        (1120, 635),
        [
            "Haidian probability" if not zh else "海淀真实概率",
            "Land value / ridership" if not zh else "地价 / 客流预测",
        ],
        lang=lang,
        size=20,
        gap=14,
        fill=RED,
    )
    footer(
        draw,
        "Source: smoke-v1 summary.json · engine commit 524ee2f · synthetic mechanism qualification"
        if not zh
        else "来源：smoke-v1 summary.json · engine commit 524ee2f · synthetic 机制资格化",
        lang=lang,
    )
    return image


def save_all(output: Path, summary_path: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    builders: dict[str, Callable[[str], Image.Image]] = {
        "site-overview": site_overview,
        "land-use-structure": scope_structure,
        "key-areas": key_areas,
        "mobility-bluegreen": mobility_bluegreen,
        "metrics-evidence": lambda lang: metrics_evidence(lang, summary),
    }
    written: list[Path] = []
    for name, builder in builders.items():
        for lang in ("zh", "en"):
            suffix = "" if lang == "zh" else ".en"
            path = output / f"{name}{suffix}.png"
            builder(lang).save(path, format="PNG", optimize=False, compress_level=9)
            written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    for path in save_all(args.output, args.summary):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
