#!/usr/bin/env python3.11
"""Figures for the Observatory release replay, from analyze_revisions.py's outputs.

fig_cascade     share of the Tranco top million at each step of the cascade, per release pair
fig_location    where in the score range the sites whose score changed were, per release pair
fig_rank        exposure and score change by Tranco rank stratum, for the two bonus releases

Palettes are the dataviz skill's validated defaults: the ordinal blue ramp 250/400/500/650 for the
four cascade steps (checked with validate_palette.js --ordinal) and categorical slots 1 and 2
(blue, orange) for the two releases. Every series also has its own marker shape, so the figures
read in grayscale print.

  python3.11 audit/scripts/observatory_replay/figures.py --in outputs/observatory_tranco_2026-09-27
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
STEPS = [("E", "exposed", "#86b6ef", "o"), ("T", "test outcome changed", "#3987e5", "s"),
         ("S", "score changed", "#256abf", "D"), ("G", "grade changed", "#104281", "^")]
RELEASE_COLORS = {"1.4.9->1.5.0": ("#2a78d6", "o"), "1.6.3->1.7.0": ("#eb6834", "s")}
STRATA = ["T1", "T2", "T3", "T4", "T5"]
STRATUM_LABEL = {"T1": "1–10k", "T2": "10k–50k", "T3": "50k–100k", "T4": "100k–500k", "T5": "500k–1M"}
FLOOR = 0.001   # log-axis position used to draw an exact zero

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42})


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float, float]:
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return 100 * p, 100 * (c - h) / d, 100 * (c + h) / d


def style(ax, xlabel: str) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)


def fig_cascade(res: dict, out: Path) -> None:
    pairs = [p for p in res["pairs"] if p["class"] in ("scoring", "defensive")]
    controls = [p for p in res["pairs"] if p["class"] in ("null", "refactor")]
    # 1.3.8 -> 1.4.0: the registered exposure predicate split CSP values on commas, which 1.3.8's
    # parser does not; the figure shows the predicate as that parser reads it (analysis key E_unsplit)
    def label(p):
        return p["pair"].replace("->", " → ") + (" *" if p["pair"] == "1.3.8->1.4.0" else "")
    labels = [label(p) for p in pairs] + [f"{len(controls)} null and refactor pairs"]
    fig, ax = plt.subplots(figsize=(3.33, 0.26 * len(labels) + 0.75))
    for i, p in enumerate(pairs):
        y = len(labels) - 1 - i
        for j, (key, _, color, marker) in enumerate(STEPS):
            w = p["weighted_top1M"][key]
            if key == "E" and "weighted_top1M_E_unsplit" in p:
                w = p["weighted_top1M_E_unsplit"]
            if w is None:
                continue
            x = max(w["pct"], FLOOR)
            lo, hi = max(w["ci95"][0], FLOOR), max(w["ci95"][1], FLOOR)
            off = (j - 1.5) * 0.12
            ax.plot([lo, hi], [y + off] * 2, color=color, linewidth=0.8)
            ax.plot(x, y + off, marker=marker, color=color, markersize=3.5, markeredgecolor="white",
                    markeredgewidth=0.4, linestyle="none")
    worst = max(p["T"] for p in controls) if controls else 0
    note = ("no site changed any test outcome" if worst == 0
            else f"at most {worst} sites changed a test outcome in any one pair")
    ax.text(FLOOR * 1.3, 0, note, va="center", color=MUTED, fontsize=6)
    ax.set_xscale("log")
    ax.set_xlim(FLOOR * 0.8, 100)
    ax.set_ylim(-0.7, len(labels) - 0.4)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(list(reversed(labels)))
    ax.set_xticks([FLOOR, 0.01, 0.1, 1, 10, 100])
    ax.set_xticklabels(["0", "0.01", "0.1", "1", "10", "100"])
    style(ax, "% of Tranco top 1M (weighted, 95 % CI)")
    handles = [plt.Line2D([], [], marker=m, color=c, linestyle="none", markersize=4, label=l)
               for _, l, c, m in STEPS]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False,
              fontsize=6, handletextpad=0.2, columnspacing=0.8)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_cascade.{ext}", dpi=300)
    plt.close(fig)


def fig_location(inp: Path, res: dict, out: Path) -> None:
    bands = [("below 70 (B− or lower)", lambda s: s < 70, "#86b6ef"),
             ("70–89 (B to A−)", lambda s: 70 <= s < 90, "#3987e5"),
             ("90 or more (A, A+)", lambda s: s >= 90, "#104281")]
    rows = []
    for p in res["pairs"]:
        if p["S"] == 0:
            continue
        f = inp / "analysis" / f"rows_{p['pair'].replace('->', '_to_')}.jsonl.gz"
        changed = [r for r in map(json.loads, gzip.open(f, "rt")) if r.get("S")]
        rows.append((p["pair"], changed))
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(3.33, 0.3 * len(rows) + 0.8))
    for i, (pair, changed) in enumerate(rows):
        y = len(rows) - 1 - i
        left = 0.0
        n = len(changed)
        for name, pred, color in bands:
            share = 100 * sum(1 for r in changed if pred(r["score_old"])) / n
            ax.barh(y, share, left=left, color=color, edgecolor="white", linewidth=1, height=0.6,
                    label=name if i == 0 else None)
            left += share
        ax.text(101, y, f"n = {n}", va="center", fontsize=6, color=MUTED)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0].replace("->", " → ") for r in reversed(rows)])
    ax.set_xlim(0, 100)
    style(ax, "% of score changes, by score under the older release")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False, fontsize=6)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_location.{ext}", dpi=300)
    plt.close(fig)


def fig_rank(res: dict, out: Path) -> None:
    by_pair = {p["pair"]: p for p in res["pairs"]}
    fig, axes = plt.subplots(1, 2, figsize=(3.33, 2.1), sharey=True,
                             gridspec_kw={"wspace": 0.12, "left": 0.24, "right": 0.97,
                                          "top": 0.74, "bottom": 0.2})
    for ax, key, title in ((axes[0], "E", "exposed"), (axes[1], "S", "score changed")):
        for k, (pair, (color, marker)) in enumerate(RELEASE_COLORS.items()):
            p = by_pair.get(pair)
            if not p:
                continue
            for i, st in enumerate(STRATA):
                ps = p["per_stratum"][st]
                if ps["n"] == 0:
                    continue
                est, lo, hi = wilson(ps[key], ps["n"])
                y = len(STRATA) - 1 - i + (k - 0.5) * 0.25
                ax.plot([lo, hi], [y, y], color=color, linewidth=0.8)
                ax.plot(est, y, marker=marker, color=color, markersize=3.5, linestyle="none",
                        markeredgecolor="white", markeredgewidth=0.4,
                        label=pair.replace("->", " → ") if i == 0 else None)
        ax.set_title(title, fontsize=7, color=INK, pad=3)
        style(ax, "% of stratum")
        ax.set_xlim(left=0)
    axes[0].set_yticks(range(len(STRATA)))
    axes[0].set_yticklabels([STRATUM_LABEL[s] for s in reversed(STRATA)])
    axes[0].set_ylabel("Tranco rank")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=6,
               bbox_to_anchor=(0.6, 1.0))
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_rank.{ext}", dpi=300)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    a = ap.parse_args()
    inp = ROOT / a.inp
    res = json.loads((inp / "analysis/results.json").read_text())
    out = inp / "figures"
    out.mkdir(exist_ok=True)
    fig_cascade(res, out)
    fig_location(inp, res, out)
    fig_rank(res, out)
    print("written:", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
