#!/usr/bin/env python3.11
"""Figures for the plan-validity analysis, from plan_validity.py's outputs.

fig_plan_fate   per scoring-relevant release pair and target, the number of sites whose recommended
                plan fails under the newer release, and whose recommendation changes while every old
                plan still works
fig_plan_age    plans made under one release and scored under a later one: the share of sites
                needing a plan for which at least one recommended plan fails, one panel per target

Colours: the dataviz skill's diverging poles, red #c93a3a for a failing plan and blue #2a78d6 for a
changed recommendation that still works (checked with validate_palette.js: all checks pass in light
mode), and its sequential blue ramp for the heatmap. Markers differ in shape as well as colour, so
the figures read in grayscale print. Style follows figures.py.

  python3.11 audit/scripts/observatory_replay/plan_validity_figures.py --in outputs/observatory_tranco_2026-09-27
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
FAIL, CHANGED = ("#c93a3a", "D"), ("#2a78d6", "o")
FLOOR = 0.001
TARGETS = [(70, "B (70)"), (90, "A (90)"), (100, "A+ (100)")]
RAMP = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42})


def save(fig, out: Path, name: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=300)
    plt.close(fig)


def fig_plan_fate(res: dict, out: Path) -> None:
    """Counts of sites, not weighted shares: a single top-10k site is about 0.0001 % of the top
    million, which a log axis of shares would draw as zero."""
    pairs = [(k, p) for k, p in res["consecutive_pairs"].items() if p["class"] not in ("null", "refactor")]
    controls = [p for p in res["consecutive_pairs"].values() if p["class"] in ("null", "refactor")]
    # control pairs checked on the 2,205-site sample (D18, D19) count as controls too
    sampled = res.get("sampled_control_pairs", {})
    n_ctrl = len(controls) + sum(1 for k, p in sampled.items() if p["class"] in ("null", "refactor"))
    sampled_differ = sum(p["vectors_differ"] for p in sampled.values())
    labels = [k.replace("->", " → ") for k, _ in pairs] + [f"{n_ctrl} null and refactor pairs"]
    floor = 0.35
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 0.24 * len(labels) + 0.85), sharey=True)
    for ax, (T, title) in zip(axes, TARGETS):
        for i, (k, p) in enumerate(pairs):
            y = len(labels) - 1 - i
            x = p[f"all512_T{T}"]
            fail = x["status"].get("SOME", 0) + x["status"].get("NONE", 0)
            for off, n, (color, marker) in ((0.13, fail, FAIL), (-0.13, x["changed_valid"], CHANGED)):
                ax.plot(max(n, floor), y + off, marker=marker, color=color, markersize=3.5,
                        markeredgecolor="white", markeredgewidth=0.4, linestyle="none")
                if n:
                    ax.text(n * 1.25, y + off, str(n), va="center", fontsize=5, color=MUTED)
        changed = sum(p["vectors_differ_sites"] for p in controls) + sampled_differ
        ax.text(floor * 1.3, 0, "no plan changed" if changed == 0 else f"vectors differ on {changed} sites",
                va="center", color=MUTED, fontsize=6)
        ax.set_xscale("log")
        ax.set_xlim(floor * 0.8, 3000)
        ax.set_xticks([floor, 1, 10, 100, 1000])
        ax.set_xticklabels(["0", "1", "10", "100", "1000"])
        ax.set_title(f"Target {title}", fontsize=7, color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
    axes[0].set_ylim(-0.7, len(labels) - 0.4)
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_yticklabels(list(reversed(labels)))
    n = f"{res['n_sites']:,}".replace(",", "\u2009")
    axes[1].set_xlabel(f"websites, of {n} scored")
    handles = [plt.Line2D([], [], marker=FAIL[1], color=FAIL[0], linestyle="none", markersize=4,
                          label="a recommended plan no longer reaches the target"),
               plt.Line2D([], [], marker=CHANGED[1], color=CHANGED[0], linestyle="none", markersize=4,
                          label="recommendation changes, every old plan still reaches it")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=6,
               handletextpad=0.2, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, out, "fig_plan_fate")


def fig_plan_age(inp: Path, out: Path, classes: list[tuple[str, str]]) -> None:
    rows_ = list(csv.DictReader(open(inp / "analysis" / "plan_age.csv")))
    get = {(r["old"], r["new"], int(r["target"])): r for r in rows_}
    made, scored = classes[:-1], classes[1:]          # the first column and last row are always empty
    cmap = LinearSegmentedColormap.from_list("blue", RAMP)
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.35))
    for ax, (T, title) in zip(axes, TARGETS):
        cells = {}
        for i, (vo, _) in enumerate(made):
            for j, (vn, _) in enumerate(scored):
                if j < i:
                    continue
                r = get[(vo, vn, T)]
                cells[(i, j)] = (100 * int(r["any_invalid"]) / int(r["eligible"]), int(r["any_invalid"]))
        vmax = max(share for share, _ in cells.values()) or 1
        for (i, j), (share, k) in cells.items():
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color=cmap(share / vmax), linewidth=0))
            ax.text(j, i, str(k), ha="center", va="center", fontsize=5,
                    color="white" if share / vmax > 0.55 else INK)
        ax.set_xlim(-0.5, len(scored) - 0.5)
        ax.set_ylim(len(made) - 0.5, -0.5)
        ax.set_xticks(range(len(scored)))
        ax.set_xticklabels([c[1] for c in scored], rotation=90, fontsize=5.5)
        ax.set_yticks(range(len(made)))
        ax.set_yticklabels([c[1] for c in made] if T == 70 else [], fontsize=5.5)
        ax.set_title(f"Target {title}", fontsize=7, color=INK)
        ax.set_xlabel("scored under", fontsize=6)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    axes[0].set_ylabel("plan made under", fontsize=6)
    fig.text(0.5, 0.005, "Cell: sites with at least one recommended plan that no longer reaches the target "
             "(shade: share of sites needing a plan, scaled per panel)", ha="center", fontsize=6, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    save(fig, out, "fig_plan_age")


def fig_margins(res: dict, out: Path, release: str = "1.6.3", target: str = "T90") -> None:
    """How far the optimal plans for A sit above 90: on the displayed score, and on the uncurved
    score that decides the grade. Two panels on one axis, bars in categorical slots 1 and 2."""
    m = res.get("uncurved_margins", {}).get(release, {}).get(target)
    if not m:
        return
    panels = [("displayed score − 90", m["displayed_margin"], "#2a78d6"),
              ("uncurved score − 90 (decides the grade)", m["uncurved_margin"], "#eb6834")]
    xs = list(range(0, 55, 5))
    fig, axes = plt.subplots(2, 1, figsize=(3.33, 2.3), sharex=True, sharey=True)
    for ax, (title, dist, color) in zip(axes, panels):
        ys = [dist.get(str(x), 0) for x in xs]
        ax.bar(xs, ys, width=3.6, color=color, linewidth=0)
        for x, y in zip(xs, ys):
            if y or x == 0:                      # the zero at 0 is the comparison, so it is labelled
                ax.text(x, y + 60, f"{y:,}".replace(",", " "), ha="center", va="bottom", fontsize=5, color=MUTED)
        ax.set_title(title, fontsize=6.5, color=INK, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
    axes[1].set_xticks(xs)
    axes[1].set_xlabel("points above the A boundary")
    axes[0].set_ylim(0, max(max(int(v) for v in d.values()) for _, d, _ in panels) * 1.25)
    fig.text(0.01, 0.5, f"optimal plans for A, release {release}", rotation=90, va="center", fontsize=6, color=INK)
    fig.tight_layout(rect=(0.03, 0, 1, 1))
    save(fig, out, "fig_margins")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default="directions/recourse_invalidation/figures_2026-10-08")
    a = ap.parse_args()
    inp = ROOT / a.inp if not Path(a.inp).is_absolute() else Path(a.inp)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    res = json.loads((inp / "analysis" / "plan_validity.json").read_text())
    fig_plan_fate(res, out)
    fig_margins(res, out)
    # one release per group of releases with identical scoring code (the 18 controls change no
    # score vector), labelled by the range it stands for
    # 1.3.8 stands for 1.3.2 to 1.3.8 (the earlier ones were searched on the D11 sample, D18 and D19)
    classes = [("1.3.8", "1.3.2–1.3.8"), ("1.4.0", "1.4.0–1.4.8"), ("1.4.9", "1.4.9"),
               ("1.5.0", "1.5.0–1.5.2"), ("1.5.3", "1.5.3–1.5.4"), ("1.6.0", "1.6.0–1.6.1"),
               ("1.6.2", "1.6.2–1.6.3"), ("1.7.0", "1.7.0–1.7.1")]
    if (inp / "analysis" / "plan_age.csv").exists():
        fig_plan_age(inp, out, classes)
    print("figures written to", out)


if __name__ == "__main__":
    main()
