#!/usr/bin/env python3.11
"""How much do the aggregate statistics a longitudinal Web study would report move between releases,
with no website changing?

Every release scored the same stored input, so any change in a population statistic between two
releases is the tool's alone. For each release (and the as-deployed jsdom configurations of D12)
this computes, over the Tranco top million with the registered weights: the share of sites at B or
better, A or better, A+ and F, the mean score, and the share of sites each test penalises. For each
consecutive pair and for the first and last releases it reports the paired change, with a 95 %
interval from 2,000 stratified bootstrap resamples of sites (seed 20260927).

  python3.11 audit/scripts/observatory_replay/aggregate_drift.py --in outputs/observatory_tranco_2026-09-27
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_revisions import FRAME, STRATA, load_inputs, load_release, vkey  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SEED = 20260927
TESTS = ["content-security-policy", "cookies", "cross-origin-resource-sharing", "redirection",
         "referrer-policy", "strict-transport-security", "subresource-integrity",
         "x-content-type-options", "x-frame-options", "cross-origin-resource-policy",
         "cross-origin-opener-policy", "cross-origin-embedder-policy"]


def stats(rel: dict, hosts: list[str]) -> dict[str, np.ndarray]:
    score = np.array([rel[h]["score"] for h in hosts], dtype=float)
    out = {"B or better": (score >= 70).astype(float), "A or better": (score >= 90).astype(float),
           "A+": (score >= 100).astype(float), "F": (score < 25).astype(float), "mean score": score}
    for t in TESTS:
        out[f"penalised by {t}"] = np.array([float(rel[h]["mods"].get(t, 0) < 0) for h in hosts])
    # outcome shares, the prevalence figures adoption studies report (e.g. scripts loaded insecurely)
    for t in TESTS:
        outcomes = [rel[h]["tests"].get(t) for h in hosts]
        for o in sorted({x for x in outcomes if x}):
            out[f"outcome {o}"] = np.array([float(x == o) for x in outcomes])
    return out


def estimate(values: np.ndarray, strata: np.ndarray, rng: np.random.Generator, draws: int = 2000):
    """Frame-weighted mean over the five Tranco strata, with a stratified bootstrap interval."""
    idx = {s: np.where(strata == s)[0] for s in STRATA}
    total = sum(FRAME.values())
    point = sum(FRAME[s] * values[idx[s]].mean() for s in STRATA) / total
    boot = np.zeros(draws)
    for s in STRATA:
        v = values[idx[s]]
        picks = rng.integers(0, len(v), size=(draws, len(v)))
        boot += FRAME[s] * v[picks].mean(axis=1)
    boot /= total
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(point), [float(lo), float(hi)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    a = ap.parse_args()
    inp = ROOT / a.inp if not Path(a.inp).is_absolute() else Path(a.inp)
    sites = load_inputs(inp)
    versions = sorted((p.name for p in (inp / "replay").iterdir()
                       if p.is_dir() and re.fullmatch(r"\d+\.\d+\.\d+", p.name)), key=vkey)
    rel = {v: load_release(inp, "replay", v) for v in versions}
    deployed = {c: load_release(inp, "sensitivity_full", c)
                for c in ["1.4.9-jsdom27.0.0", "1.5.0-jsdom27.0.1", "1.5.1-jsdom27.3.0"]}
    hosts = sorted(h for h, s in sites.items() if s["status"] == "ok" and s["stratum"] in STRATA
                   and all(rel[v].get(h, {}).get("status") == "ok" for v in versions)
                   and all(d.get(h, {}).get("status") == "ok" for d in deployed.values()))
    strata = np.array([sites[h]["stratum"] for h in hosts])
    S = {v: stats(r, hosts) for v, r in {**rel, **deployed}.items()}
    rng = np.random.default_rng(SEED)

    # levels are point estimates for outcome shares (many of them), with intervals for the rest
    levels = {v: {k: (estimate(x, strata, np.random.default_rng(SEED)) if not k.startswith("outcome ")
                      else (float(sum(FRAME[s_] * x[strata == s_].mean() for s_ in STRATA) / sum(FRAME.values())), None))
                  for k, x in S[v].items()} for v in S}
    sequences = {"registered": versions,
                 "as deployed": ["1.4.8", "1.4.9-jsdom27.0.0", "1.5.0-jsdom27.0.1", "1.5.1-jsdom27.3.0",
                                 "1.5.2", "1.5.3"]}
    changes = {}
    for name, seq in sequences.items():
        for a_, b_ in list(zip(seq, seq[1:])) + ([(seq[0], seq[-1])] if name == "registered" else []):
            row = {}
            for k in set(S[a_]) | set(S[b_]):
                zero = np.zeros(len(hosts))
                d = S[b_].get(k, zero) - S[a_].get(k, zero)
                if not d.any():
                    continue
                pt, ci = estimate(d, strata, np.random.default_rng(SEED))
                row[k] = {"change": pt, "ci95": ci, "sites_changed": int((d != 0).sum())}
            changes[f"{name}: {a_} -> {b_}"] = row
    out = inp / "analysis"
    result = {"sites": len(hosts), "note": "Tranco strata T1-T5 only; shares are fractions, mean score in points",
              "levels": levels, "changes": changes}
    (out / "aggregate_drift.json").write_text(json.dumps(result, indent=1))
    with open(out / "aggregate_drift.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["comparison", "statistic", "change", "ci_low", "ci_high", "sites_changed"])
        for comp, row in changes.items():
            for k, x in row.items():
                w.writerow([comp, k, round(x["change"], 6), round(x["ci95"][0], 6), round(x["ci95"][1], 6),
                            x["sites_changed"]])
    for comp, row in changes.items():
        if row:
            print(comp)
            for k, x in sorted(row.items(), key=lambda z: -abs(z[1]["change"]))[:6]:
                unit = "" if k == "mean score" else " pp"
                scale = 1 if k == "mean score" else 100
                print(f"   {k:45s} {scale * x['change']:+.3f}{unit} [{scale * x['ci95'][0]:+.3f}, "
                      f"{scale * x['ci95'][1]:+.3f}]  sites changed {x['sites_changed']}")


if __name__ == "__main__":
    main()
