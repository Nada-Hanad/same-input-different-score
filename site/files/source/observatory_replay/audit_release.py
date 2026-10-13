#!/usr/bin/env python3.11
"""Audit a candidate Observatory release against the deployed one before it ships.

The fixed-input replay as a pre-deployment check: the candidate (any installed configuration, for
instance an unreleased commit) and the baseline score the same stored inputs, and the report lists
what the candidate would change for the scored sites: test outcomes, scores, grades, boundary
crossings, and whether the remediation plans the baseline recommends still reach their target
(PLAN_VALIDITY_PRESPEC_2026-10-08.md). It also reports whether the algorithm version moves, which is
the only signal a scored site receives today.

Each configuration needs a replay (run_replay.py --mode replay --out-sub <dir>) and, for the plan
part, a 512-subset search (run_replay.py --mode remediate --max-size 9 --out-sub <dir>). A baseline
that is one of the 27 releases is read from replay/ and remediation_full/.

  python3.11 audit_release.py --in outputs/observatory_tranco_2026-09-27 --baseline 1.7.1 \\
      --candidate main-093035e3 [--candidate-replay candidate_replay] [--candidate-plans candidate_remediation_full]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_revisions import STRATA, load_inputs, load_release  # noqa: E402
from plan_validity import (SPACES, TARGETS, compare, population, strip)  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
BOUNDARIES = (65, 70, 90, 100)
NEW_TEST_DEFAULTS = {"cross-origin-opener-policy": "coop-not-implemented",
                     "cross-origin-embedder-policy": "coep-not-implemented"}


def where(inp: Path, sub: str, config: str) -> Path | None:
    d = inp / sub / config
    return d if d.is_dir() and len(list(d.glob("*.meta.json"))) >= 53 else None


def vectors(inp: Path, sub: str, config: str, hosts: list[str]) -> np.ndarray | None:
    if where(inp, sub, config) is None:
        return None
    rows = load_release(inp, sub, config)
    return np.array([rows[h]["scores"] for h in hosts], dtype=np.int16)


def algorithm(inp: Path, sub: str, config: str) -> set:
    return {json.loads(p.read_text())["algorithm_version"] for p in (inp / sub / config).glob("*.meta.json")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline-replay", default="replay")
    ap.add_argument("--baseline-plans", default="remediation_full")
    ap.add_argument("--candidate-replay", default="candidate_replay")
    ap.add_argument("--candidate-plans", default="candidate_remediation_full")
    a = ap.parse_args()
    inp = ROOT / a.inp if not Path(a.inp).is_absolute() else Path(a.inp)

    sites = load_inputs(inp)
    base = load_release(inp, a.baseline_replay, a.baseline)
    cand = load_release(inp, a.candidate_replay, a.candidate)
    hosts = sorted(h for h, s in sites.items() if s["status"] == "ok" and s["stratum"]
                   and base.get(h, {}).get("status") == "ok")
    status_moves = Counter((base[h]["status"], cand.get(h, {}).get("status")) for h in hosts
                           if cand.get(h, {}).get("status") != "ok")
    hosts = [h for h in hosts if cand.get(h, {}).get("status") == "ok"]
    strata = np.array([sites[h]["stratum"] for h in hosts])
    in_frame = strata != "P"

    tests_changed, score_moves, grade_moves = Counter(), Counter(), Counter()
    T, S, G = [], [], []
    X = {b: [] for b in BOUNDARIES}
    examples = []
    for h in hosts:
        o, n = base[h], cand[h]
        ch = [t for t in set(o["tests"]) | set(n["tests"])
              if o["tests"].get(t, NEW_TEST_DEFAULTS.get(t)) != n["tests"].get(t, NEW_TEST_DEFAULTS.get(t))]
        tests_changed.update(ch)
        T.append(bool(ch))
        S.append(o["score"] != n["score"])
        G.append(o["grade"] != n["grade"])
        for b in BOUNDARIES:
            X[b].append((o["score"] >= b) != (n["score"] >= b))
        if o["score"] != n["score"]:
            score_moves[n["score"] - o["score"]] += 1
        if o["grade"] != n["grade"]:
            grade_moves[f"{o['grade']}->{n['grade']}"] += 1
        if ch and len(examples) < 25:
            examples.append({"host": h, "tests": {t: [o["tests"].get(t), n["tests"].get(t)] for t in ch},
                             "score": [o["score"], n["score"]], "grade": [o["grade"], n["grade"]]})
    T, S, G = map(np.array, (T, S, G))
    report = {
        "baseline": a.baseline, "candidate": a.candidate,
        "algorithm_version": {"baseline": sorted(algorithm(inp, a.baseline_replay, a.baseline)),
                              "candidate": sorted(algorithm(inp, a.candidate_replay, a.candidate))},
        "sites_compared": len(hosts),
        "status_changes": {f"{k[0]}->{k[1]}": v for k, v in status_moves.items()},
        "test_outcome_changed": int(T.sum()), "tests_changed": dict(tests_changed),
        "score_changed": int(S.sum()), "grade_changed": int(G.sum()),
        **{f"crossed_{b}": int(np.sum(X[b])) for b in BOUNDARIES},
        "score_moves": dict(score_moves), "grade_moves": dict(grade_moves),
        "weighted_score_changed": population(S & in_frame, in_frame, strata),
        "weighted_grade_changed": population(G & in_frame, in_frame, strata),
        "examples": examples,
    }
    Vo = vectors(inp, a.baseline_plans, a.baseline, hosts)
    Vn = vectors(inp, a.candidate_plans, a.candidate, hosts)
    if Vo is not None and Vn is not None:
        report["plan_vectors_differ_sites"] = int((Vo != Vn).any(1).sum())
        for T_ in TARGETS:
            r = compare(Vo, Vn, T_, SPACES["all512"], strata, hosts)
            m = r.pop("_masks")
            r["weighted_any_invalid_all_sites"] = population(m["any_invalid"] & in_frame, in_frame, strata)
            report[f"plans_T{T_}"] = strip(r)
    else:
        report["plans"] = "no 512-subset search for one of the configurations yet"
    out = inp / "analysis" / f"release_audit_{a.baseline}_vs_{a.candidate}.json"
    out.write_text(json.dumps(report, indent=1, default=int))
    print(json.dumps({k: v for k, v in report.items() if k != "examples"}, indent=1, default=int))


if __name__ == "__main__":
    main()
