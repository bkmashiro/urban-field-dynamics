#!/usr/bin/env python3
"""Generate the offline bilingual smoke replay from frozen JSON evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def compact_json(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render(lang: str, config_json: str, result_json: str, metrics_json: str) -> str:
    zh = lang == "zh"
    title = "Urban Field Dynamics｜城市场演化系统" if zh else "Urban Field Dynamics"
    strings = {
        "scope": "Synthetic 机制资格化 · 不是海淀预测"
        if zh
        else "Synthetic mechanism qualification · not a Haidian forecast",
        "lead": "我们不优化一个终局；我们比较城市在不同政策与随机世界中如何演化。"
        if zh
        else "We do not optimise one end state; we compare how the city evolves across policies and random worlds.",
        "arm": "政策 / ablation" if zh else "Policy / ablation",
        "world": "World ID（matched seed）" if zh else "World ID (matched seed)",
        "year": "观察年份" if zh else "Observation year",
        "total": "五年更新总数" if zh else "Five-year redevelopments",
        "worlds": "出现更新的 worlds" if zh else "Worlds with redevelopment",
        "mean": "每 world 平均" if zh else "Mean per world",
        "hard": "Hard pin 转换" if zh else "Hard-pin conversions",
        "units": "单位状态回放" if zh else "Unit-state replay",
        "unit": "Synthetic unit" if zh else "Synthetic unit",
        "use": "当前用途" if zh else "Current use",
        "access": "可达性" if zh else "Accessibility",
        "shock": "当年 development shock" if zh else "Development shock this year",
        "redevelopment": "更新年份" if zh else "Redevelopment year",
        "notyet": "未更新" if zh else "not redeveloped",
        "inertia": "inertia on" if zh else "inertia on",
        "noinertia": "inertia ablated" if zh else "inertia ablated",
        "distribution": "Matched-world 对比" if zh else "Matched-world comparison",
        "supports": "当前证据支持" if zh else "What current evidence supports",
        "supports_body": "同一 world ID 在各 policy arm 复用相同 event tapes；P1 路径和 transition inertia 都会改变 synthetic 更新结果；hard pin 始终保持。"
        if zh
        else "Each world ID reuses the same event tapes across policy arms. P1 and transition inertia change synthetic redevelopment outcomes, while the hard pin remains fixed.",
        "limits": "当前证据不支持" if zh else "What current evidence does not support",
        "limits_body": "不能推断海淀真实更新概率、地价、客流、环境改善或审定规划指标。缺失官方 polygon、建筑、权属、OD、容量和历史变化数据。"
        if zh
        else "It does not estimate Haidian redevelopment probability, value, ridership, environmental benefit, or statutory controls. Official polygons, buildings, ownership, OD, capacity, and historical transitions are missing.",
        "source": "来源：smoke-v1 · 8 matched worlds · 24 runs · engine 0.1.0 / commit 524ee2f"
        if zh
        else "Source: smoke-v1 · 8 matched worlds · 24 runs · engine 0.1.0 / commit 524ee2f",
        "language": "English" if zh else "中文",
        "language_href": "index.en.html" if zh else "index.html",
    }
    labels = json.dumps(strings, ensure_ascii=False).replace("<", "\\u003c")
    metrics = json.loads(metrics_json)["metrics"]
    site_area = metrics["site_area_sqm"]["value"]
    green_ratio = metrics["green_ratio"]["value"]
    public_ratio = metrics["public_space_ratio"]["value"]
    coverage = (
        [
            ("总览地图", "provisional boundary + evidence chain"),
            ("三层范围", "统筹 / 总体 / 重点区 × 四个时间尺度"),
            ("重点区域", "众智园 / AI 原点社区 / 大钟寺"),
            ("用地分区", "Commitment / Optionality / Trigger 概念分区"),
            ("交通慢行", "fast surrogate → selected-scenario oracle"),
            ("蓝绿公共空间", "hard Pin 候选与可逆公共界面"),
            ("建筑", "更新周期观测样本；非现状普查"),
            ("更新项目", "低悔骨架、试验项目与 trigger gate"),
            ("AI 场景", "十类任务场景；需治理与退出机制"),
            ("核心指标", "provisional geometry + synthetic distributions"),
            ("任务覆盖", "六项 agent 任务映射至 proposal / geometry / visual"),
            ("自检状态", "deterministic / spatial / visual / professional"),
            ("来源", "公开资料、companion engine 与 frozen smoke artifacts"),
            ("假设", "official polygon、建筑、权属、OD 等仍缺失"),
        ]
        if zh
        else [
            ("Overview map", "provisional boundary + evidence chain"),
            ("Three-level scope", "coordinated / overall / key areas × four timescales"),
            ("Key areas", "Zhongzhiyuan / AI Origin Community / Dazhongsi"),
            ("Land-use zones", "Commitment / Optionality / Trigger concept zones"),
            ("Mobility and walking", "fast surrogate → selected-scenario oracle"),
            ("Blue-green public space", "hard-pin candidates and reversible interfaces"),
            ("Buildings", "renewal-cycle sample, not an existing-building survey"),
            ("Renewal projects", "no-regret backbone, trials, and trigger gates"),
            ("AI scenarios", "ten task contexts with governance and exit rules"),
            ("Core metrics", "provisional geometry + synthetic distributions"),
            ("Task coverage", "six agent tasks mapped to proposal / geometry / visual"),
            ("Self-check status", "deterministic / spatial / visual / professional"),
            ("Sources", "public references, companion engine, and frozen smoke artifacts"),
            ("Assumptions", "official polygons, buildings, ownership, and OD remain missing"),
        ]
    )
    coverage_html = "".join(
        f"<article><strong>{heading}</strong><span>{body}</span></article>"
        for heading, body in coverage
    )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="icon" href="data:,">
<style>
:root{{--bg:#f6f8f5;--paper:#fff;--ink:#172725;--muted:#60706c;--line:#bcc9c4;--teal:#167d78;--blue:#3a6ea5;--amber:#c7802b;--red:#b6534c;--green:#5a8e62}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans GB","Noto Sans CJK SC",sans-serif;line-height:1.5}}
main{{width:min(1180px,calc(100% - 40px));margin:auto;padding:36px 0 72px}} a{{color:var(--teal)}}
header{{display:grid;grid-template-columns:1fr auto;gap:20px;border-bottom:2px solid var(--line);padding-bottom:24px}} h1{{font-size:clamp(34px,5vw,66px);line-height:1.05;margin:0 0 14px;font-weight:650;letter-spacing:-.03em}} .lead{{font-size:21px;color:var(--muted);max-width:850px;margin:0}} .lang{{align-self:start;padding:8px 0;text-decoration:none;border-bottom:2px solid var(--teal)}}
.scope{{margin:24px 0 30px;border-left:5px solid var(--amber);padding:12px 18px;background:#fff7eb;font-weight:650}}
.controls{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:28px 0}} label{{display:block;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:7px}} select,input[type=range]{{width:100%;font:inherit}} select{{padding:10px 12px;border:1px solid var(--line);background:var(--paper)}} output{{font-variant-numeric:tabular-nums;color:var(--teal);font-weight:700}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);background:var(--paper);margin:28px 0 44px}} .kpi{{padding:20px;border-right:1px solid var(--line)}} .kpi:last-child{{border-right:0}} .kpi strong{{display:block;font-size:34px;line-height:1.1;font-variant-numeric:tabular-nums}} .kpi span{{font-size:14px;color:var(--muted)}}
h2{{font-size:31px;margin:44px 0 18px}} .unit{{display:grid;grid-template-columns:1.2fr repeat(4,1fr);gap:18px;align-items:center;padding:20px 0;border-top:1px solid var(--line)}} .unit:last-child{{border-bottom:1px solid var(--line)}} .unit-name{{font-weight:700}} .unit-name small{{display:block;color:var(--muted);font-weight:400}} .value strong{{display:block}} .value span{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}} .pin{{color:var(--red)}}
.compare{{display:grid;grid-template-columns:1.25fr .75fr;gap:44px}} .bars{{display:flex;align-items:flex-end;height:260px;border-left:2px solid var(--ink);border-bottom:2px solid var(--ink);padding:0 40px;gap:55px}} .bar-wrap{{height:100%;flex:1;display:flex;flex-direction:column;justify-content:flex-end;text-align:center}} .bar{{min-height:4px;background:var(--blue)}} .bar.p1{{background:var(--teal)}} .bar.ablation{{background:var(--amber)}} .bar-value{{font-size:24px;font-weight:700}} .bar-label{{font-size:14px;margin-top:8px;white-space:nowrap}}
.evidence{{border-left:4px solid var(--teal);padding-left:22px;margin-bottom:28px}} .evidence.limit{{border-color:var(--red)}} .evidence h3{{margin:0 0 8px;font-size:19px}} .evidence p{{margin:0;color:var(--muted)}} footer{{margin-top:55px;padding-top:18px;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}}
.coverage{{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}}.coverage article{{background:var(--paper);padding:15px 17px;min-height:84px}}.coverage strong,.coverage span{{display:block}}.coverage span{{color:var(--muted);font-size:13px;margin-top:5px}}.registered-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:18px 0 30px}}.registered-metrics div{{border-top:3px solid var(--teal);padding-top:10px}}.registered-metrics strong{{display:block;font-size:22px;font-variant-numeric:tabular-nums}}.registered-metrics span{{font-size:12px;color:var(--muted)}}
@media(max-width:800px){{.controls,.kpis,.compare,.coverage,.registered-metrics{{grid-template-columns:1fr}}.kpi{{border-right:0;border-bottom:1px solid var(--line)}}.unit{{grid-template-columns:1fr 1fr}}.bars{{gap:15px;padding:0 15px}}}}
@media print{{body{{background:#fff}}main{{width:auto;padding:20px}}.lang{{display:none}}}}
</style>
</head>
<body><main>
<header><div><h1>{title}</h1><p class="lead" id="lead"></p></div><a class="lang" href="{strings["language_href"]}">{strings["language"]}</a></header>
<div class="scope" id="scope"></div>
<section class="controls" aria-label="Replay controls">
<div><label for="arm" id="arm-label"></label><select id="arm"><option value="p0">P0 · baseline</option><option value="p1">P1 · accessibility</option><option value="p0-no-inertia">P0 · no inertia ablation</option></select></div>
<div><label for="world" id="world-label"></label><select id="world"></select></div>
<div><label for="year" id="year-label"></label><input id="year" type="range" min="2026" max="2030" value="2026" step="1"><output id="year-value">2026</output></div>
</section>
<section class="kpis"><div class="kpi"><strong id="total">—</strong><span id="total-label"></span></div><div class="kpi"><strong id="worlds">—</strong><span id="worlds-label"></span></div><div class="kpi"><strong id="mean">—</strong><span id="mean-label"></span></div><div class="kpi"><strong>0</strong><span id="hard-label"></span></div></section>
<h2 id="units-heading"></h2><section id="units"></section>
<h2 id="distribution-heading"></h2><section class="compare"><div class="bars" id="bars"></div><div><div class="evidence"><h3 id="supports-heading"></h3><p id="supports-body"></p></div><div class="evidence limit"><h3 id="limits-heading"></h3><p id="limits-body"></p></div></div></section>
<h2>{"提交覆盖" if zh else "Submission coverage"}</h2>
<section class="registered-metrics">
  <div><strong data-metric="site_area_sqm" data-value="{site_area}">{site_area:,.3f} m²</strong><span>site_area_sqm · provisional</span></div>
  <div><strong data-metric="green_ratio" data-value="{green_ratio}">{green_ratio:.6f}</strong><span>green_ratio · design target</span></div>
  <div><strong data-metric="public_space_ratio" data-value="{public_ratio}">{public_ratio:.6f}</strong><span>public_space_ratio · design target</span></div>
</section>
<section class="coverage">{coverage_html}</section>
<footer id="source"></footer>
</main>
<script>
const CONFIG={config_json};const RESULT={result_json};const T={labels};
for(const [id,key] of Object.entries({{lead:'lead',scope:'scope','arm-label':'arm','world-label':'world','year-label':'year','total-label':'total','worlds-label':'worlds','mean-label':'mean','hard-label':'hard','units-heading':'units','distribution-heading':'distribution','supports-heading':'supports','supports-body':'supports_body','limits-heading':'limits','limits-body':'limits_body',source:'source'}}))document.getElementById(id).textContent=T[key];
const arm=document.getElementById('arm'),world=document.getElementById('world'),year=document.getElementById('year');
for(const id of CONFIG.world_ids)world.add(new Option(String(id),String(id)));
const uses={{residential:{json.dumps("居住" if zh else "Residential")},research:{json.dumps("研发" if zh else "Research")},mixed:{json.dumps("混合" if zh else "Mixed use")},green:{json.dumps("绿地" if zh else "Green")},public_service:{json.dumps("公共服务" if zh else "Public service")}}};
function update(){{
 const armId=arm.value,wid=Number(world.value),yr=Number(year.value);document.getElementById('year-value').value=yr;
 const run=RESULT.runs.find(r=>r.arm_id===armId&&r.world.world_id===wid).world;const s=RESULT.summary.arms[armId];
 document.getElementById('total').textContent=s.total_redevelopments;document.getElementById('worlds').textContent=`${{s.worlds_with_redevelopment}} / ${{s.world_count}}`;document.getElementById('mean').textContent=s.mean_redevelopments.toFixed(2);
 document.getElementById('units').innerHTML=CONFIG.units.map(u=>{{const ry=run.redevelopment_years[u.unit_id];const changed=ry!==null&&yr>=ry;const current=changed?u.candidate_use:u.current_use;const access=Math.min(1,u.accessibility+((armId==='p1'&&yr>=2026)?.35:0));const shock=run.development_shocks[String(yr)][u.unit_id];return `<article class="unit"><div class="unit-name">${{u.unit_id}}<small>${{u.pin_kind==='hard'?'HARD PIN':(armId==='p0-no-inertia'?T.noinertia:T.inertia)}}</small></div><div class="value"><span>${{T.use}}</span><strong>${{uses[current]}}</strong></div><div class="value"><span>${{T.access}}</span><strong>${{access.toFixed(2)}}</strong></div><div class="value"><span>${{T.shock}}</span><strong>${{shock.toFixed(2)}}</strong></div><div class="value"><span>${{T.redevelopment}}</span><strong class="${{u.pin_kind==='hard'?'pin':''}}">${{ry??T.notyet}}</strong></div></article>`}}).join('');
}}
const barOrder=[['p0','P0'],['p1','P1'],['p0-no-inertia','P0 no inertia']];const max=20;document.getElementById('bars').innerHTML=barOrder.map(([id,label],i)=>{{const v=RESULT.summary.arms[id].total_redevelopments;return `<div class="bar-wrap"><div class="bar-value">${{v}}</div><div class="bar ${{i===1?'p1':i===2?'ablation':''}}" style="height:${{v/max*210}}px"></div><div class="bar-label">${{label}}</div></div>`}}).join('');
for(const control of [arm,world,year])control.addEventListener('input',update);update();
</script></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config_json = compact_json(args.config)
    result_json = compact_json(args.result)
    metrics_json = compact_json(args.metrics)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "index.html").write_text(
        render("zh", config_json, result_json, metrics_json), encoding="utf-8"
    )
    (args.output / "index.en.html").write_text(
        render("en", config_json, result_json, metrics_json), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
