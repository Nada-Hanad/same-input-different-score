#!/usr/bin/env python3.11
"""What each Observatory release did to a fixed, stored input, pair by pair.

Implements sections 5 to 9 of directions/recourse_invalidation/PREREGISTRATION_2026-09-27.md, with
the deviations logged in PREREGISTRATION_2026-09-27_DEVIATIONS.md (D1 to D6). Exposure is computed
from the stored input alone, never from a release's output, except where the registered predicate
is itself defined on the older release's test outcome (1.5.0).

Reads   <in>/shards/*.jsonl.gz, <in>/replay/<release>/*.jsonl.gz, <in>/remediation/<release>/*.jsonl.gz
Writes  <in>/analysis/results.json and <in>/analysis/pairs.csv

  python3.11 audit/scripts/observatory_replay/analyze_revisions.py --in outputs/observatory_tranco_2026-09-27
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FRAME = {"T1": 10_000, "T2": 40_000, "T3": 50_000, "T4": 400_000, "T5": 500_000}
SCORABLE: dict[str, float] = {}   # frame size times scored share, filled in main()
CONTROLS: set[str] = set()         # D11 stratified random controls, filled in main()
STRATA = list(FRAME)
BOUNDARIES = (65, 70, 90, 100)
TARGETS = (70, 90, 100)
SEED = 20260927
HTML_TYPES = {"text/html", "application/xhtml+xml"}
# size of each block of the 256 action subsets, in remediate.mjs order
BLOCKS = [(0, 1), (1, 9), (2, 36), (3, 84), (4, 126)]

# Pre-registered classification of each consecutive pair (section 6)
NULL = ["1.3.2", "1.3.5", "1.3.6", "1.3.7", "1.4.1", "1.4.2", "1.4.3", "1.4.4", "1.4.5", "1.4.6",
        "1.4.7", "1.5.0", "1.5.3", "1.6.0"]            # the older release of each null pair
REFACTOR = ["1.4.0", "1.5.1", "1.6.2", "1.7.0"]
DEFENSIVE = ["1.3.3", "1.4.8"]
SCORING = ["1.3.8", "1.4.9", "1.5.2", "1.5.4", "1.6.1", "1.6.3"]
NEW_TEST_DEFAULTS = {"cross-origin-opener-policy": "coop-not-implemented",
                     "cross-origin-embedder-policy": "coep-not-implemented"}


def vkey(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def wilson(k: int, n: int, z: float = 1.959964) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(100 * (c - h) / d, 3), round(100 * (c + h) / d, 3)]


# ---------- exposure features, from the stored input only ----------

def header_values(headers: dict, name: str) -> list[str]:
    out = []
    for k, v in headers.items():
        if k.lower() == name:
            out += v if isinstance(v, list) else [v]
    return [str(x) for x in out]


def directive_names(policy: str) -> list[str]:
    return [d.strip().split()[0].lower() for d in policy.split(";") if d.strip()]


def dup_report(values: list[str]) -> bool:
    for v in values:
        names = directive_names(v)
        if names.count("report-uri") > 1 or names.count("report-to") > 1:
            return True
    return False


def features(inp: dict) -> dict:
    resp = inp["responses"].get(inp["responses"].get("autoIs") or "auto") or {}
    headers = resp.get("headers") or {}
    equiv = dict((k.lower(), v) for k, v in (resp.get("httpEquiv") or []))
    csp_h = header_values(headers, "content-security-policy")
    csp_e = [str(x) for x in equiv.get("content-security-policy", [])]
    ctype = (header_values(headers, "content-type") or [""])[0].split(";")[0].strip().lower()
    # axios parses a JSON response into an object, and the retriever stores it as the page text
    body = inp.get("body") if isinstance(inp.get("body"), str) else ""
    jar = ((inp.get("session") or {}).get("jar") or {}).get("cookies") or []
    corp = [k for k in headers if k.lower() == "cross-origin-resource-policy"]
    return {
        # 1.4.0, as registered: header values split on commas, and http-equiv values
        "dup_report_registered": dup_report([p for v in csp_h for p in v.split(",")] + csp_e),
        # 1.4.0, as 1.3.8's parser sees it: each header value whole (diagnostic only)
        "dup_report_unsplit": dup_report(csp_h + csp_e),
        "csp_comma": any("," in v for v in csp_h + csp_e),
        "has_script": bool(re.search(r"<script", body, re.I)) and (ctype in HTML_TYPES or ctype == ""),
        "no_content_type": ctype == "",
        "coop": bool(header_values(headers, "cross-origin-opener-policy")),
        "coep": bool(header_values(headers, "cross-origin-embedder-policy")),
        "corp_array": any(isinstance(headers[k], list) and len(headers[k]) > 1 for k in corp),
        "cookie_edge": any((not c.get("key")) or ("sameSite" in c and c["sameSite"] is not None
                                                  and not isinstance(c["sameSite"], str)) for c in jar),
        "n_cookies": len(jar),
    }


# ---------- loading ----------

def load_inputs(inp: Path) -> dict:
    sites = {}
    for f in sorted((inp / "shards").glob("*.jsonl.gz")):
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            status = ("error" if r.get("error") else "unscannable" if r.get("unscannable")
                      else "ok" if r.get("roundtrip_ok") else "roundtrip_fail")
            prev = sites.get(r["host"])
            # a retry replaces a failed first attempt, never a successful one
            if prev and prev["status"] == "ok":
                continue
            sites[r["host"]] = {
                "stratum": r.get("stratum"), "status": status, "error": r.get("error"),
                "live": r.get("live"), "features": features(r["input"]) if r.get("input") else None,
                "collected_at": r.get("collected_at"),
            }
    return sites


def load_release(inp: Path, sub: str, v: str) -> dict:
    out = {}
    for f in sorted((inp / sub / v).glob("*.jsonl.gz")):
        for line in gzip.open(f, "rt"):
            if line.strip():
                r = json.loads(line)
                out[r["host"]] = r
    return out


# ---------- per-pair comparison ----------

def tests_changed(a: dict, b: dict) -> list[str]:
    changed = []
    for name in set(a["tests"]) | set(b["tests"]):
        if name in a["tests"] and name in b["tests"]:
            if a["tests"][name] != b["tests"][name]:
                changed.append(name)
        else:
            outcome = b["tests"].get(name, a["tests"].get(name))
            if outcome != NEW_TEST_DEFAULTS.get(name):
                changed.append(name)
    return changed


def exposure(v_old: str, feat: dict, old: dict, new: dict) -> dict[str, bool]:
    """Registered predicate E for the pair starting at v_old; extra keys are diagnostics."""
    xfo = old.get("tests", {}).get("x-frame-options")
    return {
        "1.3.3": {"E": feat["cookie_edge"] or old.get("status") == "throw"},
        "1.3.8": {"E": feat["dup_report_registered"], "E_unsplit": feat["dup_report_unsplit"]},
        "1.4.8": {"E": feat["no_content_type"] or old.get("status") == "throw"},
        "1.4.9": {"E_registered": xfo == "x-frame-options-implemented-via-csp",
                  "E": xfo == "x-frame-options-sameorigin-or-deny"},       # D5
        "1.5.2": {"E": feat["has_script"]},
        "1.5.4": {"E": feat["has_script"]},
        "1.6.1": {"E": feat["csp_comma"]},
        "1.6.3": {"E": feat["coop"] or feat["coep"] or feat["corp_array"]},
    }.get(v_old, {"E": False})


def min_actions(scores: list, target: int) -> int | None:
    i = 0
    for k, size in BLOCKS:
        block = scores[i:i + size]
        if any(s is not None and s >= target for s in block):
            return k
        i += size
    return None


def weighted(per_stratum: dict, rng: np.random.Generator, draws: int = 2000,
             sizes: dict | None = None) -> dict | None:
    """Population share with a stratified bootstrap interval.

    With `sizes` absent this is the registered estimator (section 9): each stratum weighted by its
    Tranco frame size. With `sizes`, each stratum is weighted by its estimated number of scorable
    sites instead (frame size times the scored share of the sample), which does not treat domains
    that have no website as if they resembled scored ones.
    """
    if any(per_stratum.get(s, (0, 0))[1] == 0 for s in STRATA):
        return None
    w = sizes or FRAME
    total = sum(w[s] for s in STRATA)
    est = sum(w[s] * per_stratum[s][0] / per_stratum[s][1] for s in STRATA) / total
    boot = np.zeros(draws)
    for s in STRATA:
        k, n = per_stratum[s]
        boot += w[s] * rng.binomial(n, k / n, draws) / n
    boot /= total
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"pct": round(100 * est, 4), "ci95": [round(100 * lo, 4), round(100 * hi, 4)]}


def compare(pair, sites, old, new, rem_old, rem_new, rng):
    v_old, v_new = pair
    rows = []
    for host, s in sites.items():
        if s["status"] != "ok" or s["stratum"] is None:
            continue
        a, b = old.get(host), new.get(host)
        if a is None or b is None:
            continue
        both = a["status"] == "ok" and b["status"] == "ok"
        e = exposure(v_old, s["features"], a, b)
        row = {"host": host, "stratum": s["stratum"], "both_ok": both,
               "status_old": a["status"], "status_new": b["status"], **e}
        if both:
            ch = tests_changed(a, b)
            row.update({
                "T": bool(ch), "tests_changed": ch,
                "mods_changed": {t: [a["mods"].get(t), b["mods"].get(t)] for t in ch},
                "S": a["score"] != b["score"], "delta": b["score"] - a["score"],
                "G": a["grade"] != b["grade"], "grade_old": a["grade"], "grade_new": b["grade"],
                "score_old": a["score"], "score_new": b["score"],
                "uncurved_old": a["uncurved"], "uncurved_new": b["uncurved"],
                **{f"X{bd}": (a["score"] >= bd) != (b["score"] >= bd) for bd in BOUNDARIES},
            })
            if rem_old is not None and rem_new is not None and host in rem_old and host in rem_new:
                ro, rn = rem_old[host], rem_new[host]
                row["memo_ok"] = ro["scores"][0] == a["score"] and rn["scores"][0] == b["score"]
                for t in TARGETS:
                    mo, mn = min_actions(ro["scores"], t), min_actions(rn["scores"], t)
                    row[f"M{t}_old"], row[f"M{t}_new"] = mo, mn
                    row[f"M{t}_changed"] = mo != mn
        rows.append(row)

    ok = [r for r in rows if r["both_ok"]]
    def count(key, subset=None):
        subset = ok if subset is None else subset
        return sum(1 for r in subset if r.get(key))
    per = {}
    for st in STRATA + ["P"]:
        sub = [r for r in ok if r["stratum"] == st]
        per[st] = {"n": len(sub), **{k: count(k, sub) for k in
                   ["E", "T", "S", "G", *[f"X{b}" for b in BOUNDARIES]]}}
    summary = {
        "pair": f"{v_old}->{v_new}",
        "status_change": dict(Counter((r["status_old"], r["status_new"]) for r in rows
                                      if r["status_old"] != r["status_new"])),
        "n_both_ok": len(ok),
        **{k: count(k) for k in ["E", "T", "S", "G", *[f"X{b}" for b in BOUNDARIES]]},
        "T_outside_E": [r["host"] for r in ok if r["T"] and not r["E"]][:50],
        "n_T_outside_E": sum(1 for r in ok if r["T"] and not r["E"]),
        "tests_changed": dict(Counter(t for r in ok for t in r["tests_changed"])),
        "delta": dict(Counter(r["delta"] for r in ok if r["S"])),
        "grade_moves": dict(Counter(f"{r['grade_old']}->{r['grade_new']}" for r in ok if r["G"])),
        "per_stratum": per,
    }
    for extra in ("E_registered", "E_unsplit"):
        if any(extra in r for r in ok):
            summary[f"n_{extra}"] = count(extra)
            summary[f"n_T_outside_{extra}"] = sum(1 for r in ok if r["T"] and not r.get(extra))
            per_x = {st: (count(extra, [r for r in ok if r["stratum"] == st]),
                          len([r for r in ok if r["stratum"] == st])) for st in STRATA}
            summary[f"weighted_top1M_{extra}"] = weighted(per_x, rng)
    with_rem = [r for r in ok if "memo_ok" in r]
    if with_rem:
        # D11: jsdom-era pairs have remediation for a host subset; rates then come from the
        # stratified random controls only, weighted like every other population figure
        subset = len(with_rem) < 0.9 * len(ok)
        pool = [r for r in with_rem if r["host"] in CONTROLS] if subset else with_rem
        summary["remediation_coverage"] = {"sites": len(with_rem), "subset": subset,
                                           "rate_pool": len(pool)}
        summary["remediation_weighted"] = {
            f"target_{t}": weighted({st: (sum(1 for r in pool if r["stratum"] == st and r.get(f"M{t}_changed")),
                                          sum(1 for r in pool if r["stratum"] == st)) for st in STRATA}, rng)
            for t in TARGETS}
    if with_rem:
        ok_rem = with_rem
        summary["remediation"] = {
            "memo_mismatch": sum(1 for r in ok_rem if r.get("memo_ok") is False),
            **{f"target_{t}": {
                "changed": sum(1 for r in ok_rem if r.get(f"M{t}_changed")),
                "increased": sum(1 for r in ok_rem if r.get(f"M{t}_changed") and _gt(r[f"M{t}_new"], r[f"M{t}_old"])),
                "decreased": sum(1 for r in ok_rem if r.get(f"M{t}_changed") and _gt(r[f"M{t}_old"], r[f"M{t}_new"])),
                "changed_outside_E": sum(1 for r in ok_rem if r.get(f"M{t}_changed") and not r["E"]),
                "changed_among_controls": sum(1 for r in ok_rem if r["host"] in CONTROLS and r.get(f"M{t}_changed")),
            } for t in TARGETS}}
    summary["weighted_top1M"] = {k: weighted({s: (per[s][k], per[s]["n"]) for s in STRATA}, rng)
                                 for k in ["E", "T", "S", "G"]}
    summary["weighted_scorable"] = {k: weighted({s: (per[s][k], per[s]["n"]) for s in STRATA}, rng,
                                                sizes=SCORABLE) for k in ["E", "T", "S", "G"]}
    summary["pct_of_both_ok"] = {k: {"pct": round(100 * summary[k] / len(ok), 4) if ok else None,
                                     "wilson95": wilson(summary[k], len(ok))} for k in ["E", "T", "S", "G"]}
    s_rows = [r for r in ok if r["S"]]
    summary["n_S_without_T"] = sum(1 for r in s_rows if not r["T"])
    summary["S_old_uncurved_below_90"] = sum(1 for r in s_rows if r["uncurved_old"] < 90)
    summary["S_new_uncurved_below_90"] = sum(1 for r in s_rows if r["uncurved_new"] < 90)
    return summary, rows


def _gt(x, y):
    """None means unreachable within four actions, which is more than any count."""
    x = math.inf if x is None else x
    y = math.inf if y is None else y
    return x > y


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    a = ap.parse_args()
    inp = ROOT / a.inp if not Path(a.inp).is_absolute() else Path(a.inp)
    rng = np.random.default_rng(SEED)
    sites = load_inputs(inp)
    versions = sorted((p.name for p in (inp / "replay").iterdir()
                       if p.is_dir() and re.fullmatch(r"\d+\.\d+\.\d+", p.name)), key=vkey)
    releases = {v: load_release(inp, "replay", v) for v in versions}
    rem = {v: load_release(inp, "remediation", v) for v in versions if (inp / "remediation" / v).is_dir()}

    collection = {st: dict(Counter(s["status"] for s in sites.values() if s["stratum"] == st))
                  for st in STRATA + ["P"]}
    SCORABLE.update({st: FRAME[st] * collection[st].get("ok", 0) / sum(collection[st].values())
                     for st in STRATA})
    ctrl_file = inp / "analysis" / "remediation_jsdom_controls.txt"
    if ctrl_file.exists():
        CONTROLS.update(h for h in ctrl_file.read_text().split() if h)
    live = releases.get("1.7.1", {})
    v1 = Counter()
    for host, s in sites.items():
        if s["status"] != "ok":
            continue
        r = live.get(host)
        same = (r is not None and r["status"] == "ok" and r["score"] == s["live"]["score"]
                and r["grade"] == s["live"]["grade"]
                and all(r["tests"].get(k) == t for k, t in s["live"]["tests"].items()))
        v1["exact" if same else "mismatch"] += 1
    v3 = {v: dict(Counter(r["status"] for r in rel.values())) for v, rel in releases.items()}

    pairs, all_rows = [], {}
    for v_old, v_new in zip(versions, versions[1:]):
        cls = ("null" if v_old in NULL else "refactor" if v_old in REFACTOR
               else "defensive" if v_old in DEFENSIVE else "scoring" if v_old in SCORING else "?")
        summary, rows = compare((v_old, v_new), sites, releases[v_old], releases[v_new],
                                rem.get(v_old), rem.get(v_new), rng)
        summary["class"] = cls
        pairs.append(summary)
        all_rows[summary["pair"]] = rows

    out = inp / "analysis"
    out.mkdir(exist_ok=True)
    result = {"collection_status_by_stratum": collection,
              "V1_storage_fidelity": dict(v1), "V3_status_by_release": v3,
              "pairs": pairs}
    (out / "results.json").write_text(json.dumps(result, indent=1))
    with open(out / "pairs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair", "class", "n_both_ok", "E", "T", "S", "G", "X65", "X70", "X90", "X100",
                    "T_outside_E", "weighted_S_pct"])
        for p in pairs:
            ws = p["weighted_top1M"]["S"]
            w.writerow([p["pair"], p["class"], p["n_both_ok"], p["E"], p["T"], p["S"], p["G"],
                        p["X65"], p["X70"], p["X90"], p["X100"], p["n_T_outside_E"],
                        ws["pct"] if ws else ""])
    # per-site rows for the scoring pairs, for figures and audit
    for pair, rows in all_rows.items():
        if any(r.get("T") or r.get("S") for r in rows):
            with gzip.open(out / f"rows_{pair.replace('->', '_to_')}.jsonl.gz", "wt") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
    print(json.dumps({"V1": dict(v1), "collection": collection}, indent=1))
    for p in pairs:
        print(f"{p['pair']:>16} {p['class']:>9}  n={p['n_both_ok']:>6}  E={p['E']:>5}  T={p['T']:>5}  "
              f"S={p['S']:>5}  G={p['G']:>5}  T-outside-E={p['n_T_outside_E']}")


if __name__ == "__main__":
    main()
