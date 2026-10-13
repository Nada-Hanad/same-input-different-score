#!/usr/bin/env python3.11
"""Do the remediation plans recommended under one Observatory release still reach their target under a later one?

Implements directions/recourse_invalidation/PLAN_VALIDITY_PRESPEC_2026-10-08.md (deviations D13 and D14)
on the 512-subset score vectors that remediate.mjs --max-size 9 wrote for every release, with the
exploratory additions of D15 (margins, uncurved scores), D16 (candidate audit, in audit_release.py)
and D17 (as-deployed jsdom configurations searched on the sites where they differ). A plan is a
subset of the nine header actions; applying it under a later release and scoring the result is that
release's score for the same subset on the same stored input, so no new scan is needed here.

Reads   <in>/shards (strata and exposure features, through analyze_revisions.load_inputs),
        <in>/replay/<release> (per-test modifiers, for the scanner-guided plan R3),
        <in>/remediation_full/<release>, and <in>/remediation/<release> for the prefix check,
        <in>/remediation_uncurved/<release>, <in>/remediation_targeted/<config>, <in>/sensitivity_full/<config>
Writes  <in>/analysis/plan_validity.json, plan_age.csv, plan_validity_units/<pair>.jsonl.gz,
        and a cache of the score matrices, plan_vectors.npz

  python3.11 audit/scripts/observatory_replay/plan_validity.py --in outputs/observatory_tranco_2026-09-27
"""
from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_revisions import (FRAME, STRATA, NULL, REFACTOR, DEFENSIVE, SCORING,  # noqa: E402
                               load_inputs, load_release, vkey, weighted)

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "directions/recourse_invalidation/reference_pack/Observatory_paper_reference_2026-09-28/derived/release_ledger.csv"
SEED = 20260927
TARGETS = (70, 90, 100)
ACTIONS = ["csp", "hsts", "xfo", "xcto", "referrer", "corp", "coop", "coep", "cookies"]
# the test each action is named for, for the scanner-guided plan; redirection, SRI and CORS have none
TEST_ACTION = {"content-security-policy": 0, "strict-transport-security": 1, "x-frame-options": 2,
               "x-content-type-options": 3, "referrer-policy": 4, "cross-origin-resource-policy": 5,
               "cross-origin-opener-policy": 6, "cross-origin-embedder-policy": 7, "cookies": 8}
INF = 99

# subsets in remediate.mjs order: by size, then lexicographic; the first 256 are the depth-four search
SUBSETS = [()] + [c for k in range(1, 10) for c in itertools.combinations(range(9), k)]
MASK = np.array([sum(1 << i for i in s) for s in SUBSETS])
SIZE = np.array([len(s) for s in SUBSETS])
POS = {int(m): j for j, m in enumerate(MASK)}
SUP = (MASK[:, None] & MASK[None, :]) == MASK[:, None]          # SUP[a, b]: subset b contains subset a
SPACES = {"all512": np.ones(512, bool), "depth4": SIZE <= 4}


def names(col: int) -> list[str]:
    return [ACTIONS[i] for i in SUBSETS[col]]


def pair_class(v_old: str) -> str:
    return ("null" if v_old in NULL else "refactor" if v_old in REFACTOR
            else "defensive" if v_old in DEFENSIVE else "scoring" if v_old in SCORING else "?")


# ---------- loading ----------

def load_vectors(inp: Path, versions: list[str], hosts: list[str],
                 cache_name: str = "plan_vectors.npz") -> dict[str, np.ndarray]:
    """Score matrices (site x 512 subsets) per release, cached in analysis/<cache_name>."""
    cache = inp / "analysis" / cache_name
    have = {}
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        if list(z["hosts"]) == hosts:
            have = {k: z[k] for k in z.files if k != "hosts"}
    index = {h: i for i, h in enumerate(hosts)}
    out = {}
    for v in versions:
        if v in have:
            out[v] = have[v]
            continue
        metas = list((inp / "remediation_full" / v).glob("*.meta.json"))
        if len(metas) < 53:
            print(f"  {v}: {len(metas)} of 53 shards searched, skipped for now", flush=True)
            continue
        m = np.full((len(hosts), 512), -1, np.int16)
        for r in load_release(inp, "remediation_full", v).values():
            i = index.get(r["host"])
            if i is None:
                continue
            if r["status"] != "ok" or any(s is None for s in r["scores"]):
                raise SystemExit(f"{v} {r['host']}: status {r['status']}, cannot analyse")
            m[i] = r["scores"]
        missing = int((m[:, 0] < 0).sum())
        if missing:
            raise SystemExit(f"{v}: {missing} scored sites have no vector")
        out[v] = m
    np.savez_compressed(cache, hosts=np.array(hosts), **out)
    return out


def checks(inp: Path, V: dict, hosts: list[str], replay: dict) -> dict:
    """Prefix equality with the registered depth-four vectors, base score equal to the replay
    score, and monotonicity (adding an action never lowers a score)."""
    res = {}
    for v, m in V.items():
        c = {}
        reg = load_release(inp, "remediation", v) if (inp / "remediation" / v).is_dir() else {}
        if reg:
            idx = [i for i, h in enumerate(hosts) if h in reg]
            regm = np.array([reg[hosts[i]]["scores"] for i in idx], dtype=np.int16)
            c["registered_prefix_sites"] = len(idx)
            c["registered_prefix_mismatch"] = int((m[idx, :256] != regm).any(axis=1).sum())
        base = np.array([replay[v][h]["score"] for h in hosts])
        c["base_equals_replay"] = int((m[:, 0] == base).sum())
        viol = 0
        for b in range(9):
            without = np.where((MASK & (1 << b)) == 0)[0]
            with_b = np.array([POS[int(MASK[j]) | (1 << b)] for j in without])
            viol += int((m[:, with_b] < m[:, without]).sum())
        c["monotonicity_violations"] = viol
        res[v] = c
    return res


# ---------- plan families ----------

def families(S: np.ndarray, T: int, space: np.ndarray):
    reach = (S >= T) & space[None, :]
    k = np.where(reach, SIZE[None, :], INF).min(axis=1)
    fam = reach & (SIZE[None, :] == k[:, None])
    return reach, k, fam


def inclusion_minimal(reach: np.ndarray) -> np.ndarray:
    """Sufficient subsets from which no single action can be dropped (plan model R1)."""
    minimal = reach.copy()
    for b in range(9):
        has = (MASK & (1 << b)) != 0
        child = np.array([POS[int(m) ^ (1 << b)] if m & (1 << b) else POS[int(m)] for m in MASK])
        minimal &= ~(has[None, :] & reach[:, child])
    return minimal


def additional_effort(valid_new_row: np.ndarray, col: int, space: np.ndarray) -> int:
    cand = SUP[col] & valid_new_row & space
    return int((SIZE[cand] - SIZE[col]).min()) if cand.any() else INF


def compare(So: np.ndarray, Sn: np.ndarray, T: int, space: np.ndarray, strata: np.ndarray,
            hosts: list[str], keep_units: bool = False) -> dict:
    reach_o, k_o, fam_o = families(So, T, space)
    reach_n, k_n, fam_n = families(Sn, T, space)
    valid_n = Sn >= T
    need = So[:, 0] < T
    elig = need & (k_o < INF)
    inv = fam_o & ~valid_n
    n_opt, n_inv = fam_o.sum(1), inv.sum(1)
    status = np.where(n_inv == 0, "ALL", np.where(n_inv == n_opt, "NONE", "SOME"))
    met = Sn[:, 0] >= T
    out = k_n >= INF
    same = k_n == k_o
    identical = same & (fam_o == fam_n).all(1)
    contained = (~fam_o | fam_n).all(1)
    cat = np.select([met, out, k_n > k_o, k_n < k_o, identical, same & contained, same & ~contained],
                    ["met_without_action", "out_of_reach", "costlier", "cheaper", "identical",
                     "expanded", "hidden_invalidation"], "?")
    e = np.where(elig)[0]
    res = {
        "eligible": int(elig.sum()),
        "not_needed_under_old": int((~need).sum()),
        "lost_without_plan": int(((~need) & ~met).sum()),     # met T with no action under old, not under new
        "out_of_reach_under_old": int((need & (k_o >= INF)).sum()),
        "status": dict(Counter(status[e].tolist())),
        "plans_total": int(n_opt[e].sum()),
        "plans_invalid": int(n_inv[e].sum()),
        "mean_tie_aware_failure": float((n_inv[e] / n_opt[e]).mean()) if len(e) else None,
        "units_with_ties": int((n_opt[e] > 1).sum()),
        "category": dict(Counter(cat[e].tolist())),
        # the site's own current score gives no sign: same score under both releases
        "any_invalid_base_unchanged": int((elig & (n_inv > 0) & (So[:, 0] == Sn[:, 0])).sum()),
        "changed_base_unchanged": int((elig & (cat != "identical") & (So[:, 0] == Sn[:, 0])).sum()),
    }
    # R1 and R2: every inclusion-minimal and every sufficient plan, among sites that need a plan
    minimal = inclusion_minimal(reach_o)
    nd = np.where(need)[0]
    res["R1_inclusion_minimal"] = {"plans": int(minimal[nd].sum()),
                                   "invalid": int((minimal & ~valid_n)[nd].sum()),
                                   "sites_with_invalid": int((minimal & ~valid_n)[nd].any(1).sum())}
    res["R2_any_sufficient"] = {"plans": int(reach_o[nd].sum()),
                                "invalid": int((reach_o & ~valid_n)[nd].sum()),
                                "sites_with_invalid": int((reach_o & ~valid_n)[nd].any(1).sum())}
    # additional effort and sunk-cost excess, per unit with an invalid plan
    add_min, add_max, excess = [], [], []
    units = []
    for i in e:
        if n_inv[i] == 0 and cat[i] == "identical":
            continue
        a = [additional_effort(valid_n[i], j, space) for j in np.where(inv[i])[0]]
        if a:
            add_min.append(min(a))
            add_max.append(max(a))
            if max(a) < INF and k_n[i] < INF:
                excess.append(int(k_o[i]) + max(a) - int(k_n[i]))
        if keep_units:
            units.append({
                "host": hosts[i], "stratum": strata[i], "target": T, "category": cat[i], "status": status[i],
                "score_old": int(So[i, 0]), "score_new": int(Sn[i, 0]), "k_old": int(k_o[i]),
                "k_new": None if k_n[i] >= INF else int(k_n[i]),
                "plan_scores_old": [int(So[i, j]) for j in np.where(fam_o[i])[0]],
                "plans_old": [names(j) for j in np.where(fam_o[i])[0]],
                "plans_new": [names(j) for j in np.where(fam_n[i])[0]],
                "invalid_plans": [{"plan": names(j), "score_new": int(Sn[i, j]),
                                   "additional": None if x >= INF else x}
                                  for j, x in zip(np.where(inv[i])[0], a)],
            })
    res["additional_effort_min"] = dict(Counter(add_min))
    res["additional_effort_max"] = dict(Counter(add_max))
    res["sunk_cost_excess_worst_plan"] = dict(Counter(excess))
    cheap = e[cat[e] == "cheaper"]
    res["over_provisioning"] = dict(Counter((k_o[cheap] - np.where(k_n[cheap] >= INF, 0, k_n[cheap])).tolist()))
    # slack: how far above the target an optimal plan lands under the older release (exploratory, D15)
    slack_all = (So - T)[fam_o & elig[:, None]]
    slack_inv = (So - T)[inv & elig[:, None]]
    res["optimal_plan_slack"] = dict(Counter(slack_all.tolist()))
    res["invalid_plan_slack"] = dict(Counter(slack_inv.tolist()))
    # robust counterfactual: the cheapest plans that clear the target by a margin under the older release
    for d in (5, 10):
        _, k_d, fam_d = families(So, T + d, space)
        ok = elig & (k_d < INF)
        inv_d = fam_d & ~valid_n
        res[f"robust_margin_{d}"] = {
            "units": int(ok.sum()), "extra_actions": dict(Counter((k_d - k_o)[ok].tolist())),
            "units_with_invalid": int((ok & inv_d.any(1)).sum()),
            "units_with_invalid_among_minimal_invalid": int((ok & inv_d.any(1) & (n_inv > 0)).sum()),
            "minimal_invalid_units_covered": int((ok & (n_inv > 0)).sum()),
        }
    res["_masks"] = {"elig": elig, "any_invalid": elig & (n_inv > 0), "hidden": elig & np.isin(cat, ["expanded", "hidden_invalidation"]),
                     "count_changed": elig & np.isin(cat, ["costlier", "cheaper", "met_without_action", "out_of_reach"]),
                     "changed": elig & (cat != "identical"), "lost": (~need) & ~met,
                     "changed_valid": elig & (cat != "identical") & (n_inv == 0)}
    if keep_units:
        res["_units"] = units
    return res


def table3_check(inp: Path, So: np.ndarray, Sn: np.ndarray, key: str, hosts: list[str],
                 strata: np.ndarray | None = None) -> dict | None:
    """Recount the registered fewer/more minimum-effort changes (draft Table 3) from the new vectors,
    on the sites the registered search covered, and compare with analysis/results.json."""
    reg = {p["pair"]: p for p in json.loads((inp / "analysis" / "results.json").read_text())["pairs"]}
    rem = reg.get(key, {}).get("remediation")
    if not rem:
        return None
    covered = {}
    for v in key.split("->"):
        d = inp / "remediation" / v
        covered[v] = {r["host"] for r in load_release(inp, "remediation", v).values()} if d.is_dir() else set()
    rows = np.array([h in covered[key.split("->")[0]] and h in covered[key.split("->")[1]] for h in hosts])
    out = {"sites": int(rows.sum())}
    for T in TARGETS:
        m_o = families(So, T, SPACES["depth4"])[1]
        m_n = families(Sn, T, SPACES["depth4"])[1]
        fewer, more = int((rows & (m_n < m_o)).sum()), int((rows & (m_n > m_o)).sum())
        r = rem[f"target_{T}"]
        out[f"T{T}"] = {"fewer": fewer, "more": more, "registered_fewer": r["decreased"],
                        "registered_more": r["increased"],
                        "match": fewer == r["decreased"] and more == r["increased"]}
        if strata is not None:
            # the same quantity on every scored site, now that every release has a full vector; the
            # registered estimate for the jsdom-era pairs came from the 2,000 controls (D11)
            frame = strata != "P"
            out[f"T{T}"]["all_sites_fewer"] = int((m_n < m_o).sum())
            out[f"T{T}"]["all_sites_more"] = int((m_n > m_o).sum())
            out[f"T{T}"]["weighted_changed_all_sites"] = population((m_n != m_o) & frame, frame, strata)
            out[f"T{T}"]["registered_weighted"] = reg[key].get("remediation_weighted", {}).get(f"target_{T}")
    return out


def scanner_guided(So: np.ndarray, Sn: np.ndarray, mods_old: list[dict], T: int) -> dict:
    """Plan model R3: fix every test the older release penalises, whatever the target."""
    cols = np.array([POS[sum(1 << TEST_ACTION[t] for t, m in md.items() if m < 0 and t in TEST_ACTION)]
                     for md in mods_old])
    rows = np.arange(len(cols))
    need = So[:, 0] < T
    ok_old = So[rows, cols] >= T
    ok_new = Sn[rows, cols] >= T
    return {"need": int(need.sum()), "reaches_under_old": int((need & ok_old).sum()),
            "fails_under_new": int((need & ok_old & ~ok_new).sum()),
            "newly_reaches": int((need & ~ok_old & ok_new).sum())}


def population(mask: np.ndarray, base: np.ndarray, strata: np.ndarray) -> dict | None:
    per = {s: (int((mask & (strata == s)).sum()), int((base & (strata == s)).sum())) for s in STRATA}
    return weighted(per, np.random.default_rng(SEED))


def strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


# ---------- exposure, for expectation X4 ----------

def exposure_sets(sites: dict, hosts: list[str], replay: dict) -> dict[str, np.ndarray]:
    f = [sites[h]["features"] for h in hosts]
    sri = lambda a, b: np.array([replay[a][h]["tests"].get("subresource-integrity")
                                 != replay[b][h]["tests"].get("subresource-integrity") for h in hosts])
    out = {}
    if "1.3.8" in replay:
        out["1.3.8->1.4.0"] = np.array([x["dup_report_unsplit"] for x in f])
    for a, b in [("1.4.8", "1.4.9"), ("1.5.2", "1.5.3"), ("1.5.4", "1.6.0")]:
        if a in replay and b in replay:
            out[f"{a}->{b}"] = sri(a, b)
    out["1.6.1->1.6.2"] = np.array([x["csp_comma"] for x in f])
    if "1.7.0" in replay:
        t = [replay["1.7.0"][h]["tests"] for h in hosts]
        out["1.6.3->1.7.0"] = np.array([x["coop"] or x["coep"] or x["corp_array"] for x in f])
        out["1.6.3->1.7.0 invalid COOP/COEP or repeated CORP"] = np.array([
            t[i].get("cross-origin-opener-policy") == "coop-header-invalid"
            or t[i].get("cross-origin-embedder-policy") == "coep-header-invalid" or f[i]["corp_array"]
            for i in range(len(hosts))])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--no-age", action="store_true", help="skip the plan-age matrix")
    a = ap.parse_args()
    inp = ROOT / a.inp if not Path(a.inp).is_absolute() else Path(a.inp)
    out = inp / "analysis"

    sites = load_inputs(inp)
    versions = sorted((p.name for p in (inp / "replay").iterdir()
                       if p.is_dir() and re.fullmatch(r"\d+\.\d+\.\d+", p.name)), key=vkey)
    replay = {v: load_release(inp, "replay", v) for v in versions}
    hosts = sorted(h for h, s in sites.items() if s["status"] == "ok" and s["stratum"]
                   and all(replay[v].get(h, {}).get("status") == "ok" for v in versions))
    strata = np.array([sites[h]["stratum"] for h in hosts])
    in_frame = strata != "P"
    print(f"{len(hosts)} sites scored under every release", flush=True)

    V = load_vectors(inp, versions, hosts)
    have = [v for v in versions if v in V]
    print("releases with full vectors:", ", ".join(have), flush=True)
    result = {"prespec_sha256": (ROOT / "directions/recourse_invalidation/PLAN_VALIDITY_PRESPEC_2026-10-08.sha256")
              .read_text().split()[0], "n_sites": len(hosts), "releases_analysed": have,
              "checks": checks(inp, V, hosts, replay)}

    expo = exposure_sets(sites, hosts, replay)
    pairs = {}
    union = {T: np.zeros(len(hosts), bool) for T in TARGETS}      # failing at one or more pairs
    union_changed = {T: np.zeros(len(hosts), bool) for T in TARGETS}
    times_failed = {T: np.zeros(len(hosts), int) for T in TARGETS}   # how many pairs, per site
    times_changed = {T: np.zeros(len(hosts), int) for T in TARGETS}
    unit_dir = out / "plan_validity_units"
    unit_dir.mkdir(parents=True, exist_ok=True)
    for v_old, v_new in zip(versions, versions[1:]):
        if v_old not in V or v_new not in V:
            continue
        key = f"{v_old}->{v_new}"
        So, Sn = V[v_old], V[v_new]
        p = {"class": pair_class(v_old), "vectors_identical_sites": int((So == Sn).all(1).sum()),
             "vectors_differ_sites": int((So != Sn).any(1).sum()),
             "table3_check": table3_check(inp, So, Sn, key, hosts, strata)}
        units = []
        for space_name, space in SPACES.items():
            for T in TARGETS:
                r = compare(So, Sn, T, space, strata, hosts, keep_units=(space_name == "all512"))
                m = r.pop("_masks")
                if space_name == "all512":
                    union[T] |= m["any_invalid"]
                    union_changed[T] |= m["changed"]
                    times_failed[T] += m["any_invalid"]
                    times_changed[T] += m["changed"]
                units += r.pop("_units", [])
                r["weighted_any_invalid_all_sites"] = population(m["any_invalid"] & in_frame, in_frame, strata)
                r["weighted_any_invalid_eligible"] = population(m["any_invalid"] & in_frame, m["elig"] & in_frame, strata)
                r["weighted_hidden_all_sites"] = population(m["hidden"] & in_frame, in_frame, strata)
                r["weighted_changed_all_sites"] = population(m["changed"] & in_frame, in_frame, strata)
                r["weighted_count_changed_all_sites"] = population(m["count_changed"] & in_frame, in_frame, strata)
                r["weighted_changed_valid_all_sites"] = population(m["changed_valid"] & in_frame, in_frame, strata)
                r["changed_valid"] = int(m["changed_valid"].sum())
                if key in expo:
                    r["any_invalid_outside_exposure"] = int((m["any_invalid"] & ~expo[key]).sum())
                    r["changed_outside_exposure"] = int((m["changed"] & ~expo[key]).sum())
                if f"{key} invalid COOP/COEP or repeated CORP" in expo and T in (70, 90):
                    fine = expo[f"{key} invalid COOP/COEP or repeated CORP"]
                    r["changed_outside_invalid_or_repeated"] = int((m["changed"] & ~fine).sum())
                r["R3_scanner_guided"] = scanner_guided(So, Sn, [replay[v_old][h]["mods"] for h in hosts], T)
                p[f"{space_name}_T{T}"] = r
        pairs[key] = p
        if p["vectors_differ_sites"]:
            with gzip.open(unit_dir / f"{key.replace('->', '_to_')}.jsonl.gz", "wt") as f:
                for u in units:
                    if u["category"] != "identical":
                        f.write(json.dumps(u) + "\n")
        print(f"{key:>14} {p['class']:>9} vectors differ on {p['vectors_differ_sites']:>5} sites; "
              + "  ".join(f"T{T}: elig {p[f'all512_T{T}']['eligible']}, any-invalid "
                          f"{p[f'all512_T{T}']['status'].get('SOME', 0) + p[f'all512_T{T}']['status'].get('NONE', 0)}, "
                          f"changed {sum(c for k, c in p[f'all512_T{T}']['category'].items() if k != 'identical')}"
                          for T in TARGETS), flush=True)
    result["consecutive_pairs"] = pairs
    # D18: control releases searched on the D11 host list only; each consecutive pair that involves
    # one is compared on the sites both sides have
    sampled = {v: load_release(inp, "remediation_sample", v) for v in versions
               if v not in V and len(list((inp / "remediation_sample" / v).glob("*.meta.json"))) >= 53}
    if sampled:
        index = {h: i for i, h in enumerate(hosts)}
        def rows(v):
            if v in V:
                return {h: V[v][i] for h, i in index.items()}
            return {h: np.array(r["scores"], dtype=np.int16) for h, r in sampled.get(v, {}).items() if h in index}
        ctrl = {}
        for v_old, v_new in zip(versions, versions[1:]):
            if v_old not in sampled and v_new not in sampled:
                continue
            if (v_old not in V and v_old not in sampled) or (v_new not in V and v_new not in sampled):
                continue
            a_, b_ = rows(v_old), rows(v_new)
            common = sorted(set(a_) & set(b_))
            ctrl[f"{v_old}->{v_new}"] = {"class": pair_class(v_old), "sites_compared": len(common),
                                         "vectors_differ": int(sum(not (a_[h] == b_[h]).all() for h in common))}
        result["sampled_control_pairs"] = ctrl
        # D19: each sampled release against the nearest full-sample release on either side
        full = [w for w in versions if w in V]
        near = {}
        for v in sampled:
            for w in ([x for x in full if vkey(x) < vkey(v)][-1:] + [x for x in full if vkey(x) > vkey(v)][:1]):
                a_, b_ = rows(v), rows(w)
                common = sorted(set(a_) & set(b_))
                near[f"{v} vs {w}"] = {"sites_compared": len(common),
                                       "vectors_differ": int(sum(not (a_[h] == b_[h]).all() for h in common))}
        result["sampled_vs_full_neighbours"] = near
        result["sampled_checks"] = {
            v: {"sites": len(r), "base_equals_replay": sum(1 for h, x in r.items()
                                                           if x["scores"][0] == replay[v].get(h, {}).get("score"))}
            for v, r in sampled.items()}
    result["union_over_consecutive_pairs"] = {
        f"T{T}": {"pairs_covered": len(pairs), "sites_with_failing_plan": int(union[T].sum()),
                  "sites_with_changed_recommendation": int(union_changed[T].sum()),
                  "weighted_failing_pct_of_all": population(union[T] & in_frame, in_frame, strata),
                  "weighted_changed_pct_of_all": population(union_changed[T] & in_frame, in_frame, strata),
                  "sites_by_number_of_pairs_failing": dict(Counter(times_failed[T][times_failed[T] > 0].tolist())),
                  "sites_by_number_of_pairs_changed": dict(Counter(times_changed[T][times_changed[T] > 0].tolist()))}
        for T in TARGETS}

    # exploratory (D12): the sequence with the jsdom version each release shipped; the base replays
    # of those configurations are in sensitivity_full/
    deployed = ["1.4.8", "1.4.9-jsdom27.0.0", "1.5.0-jsdom27.0.1", "1.5.1-jsdom27.3.0", "1.5.2", "1.5.3"]
    twin = {"1.4.9-jsdom27.0.0": "1.4.9", "1.5.0-jsdom27.0.1": "1.5.0", "1.5.1-jsdom27.3.0": "1.5.1"}
    extra = list(twin)
    ready = all(v in V for v in ["1.4.8", "1.4.9", "1.5.0", "1.5.1", "1.5.2", "1.5.3"]) and all(
        len(list((inp / "remediation_targeted" / c).glob("*.meta.json"))) >= 53 for c in [*twin, *twin.values()])
    if ready:
        # D17: the shipped-jsdom configuration is searched on the sites where its base outcome differs
        # from the installed twin, plus 500 controls; the twin's vectors stand everywhere else
        sens = {c: load_release(inp, "sensitivity_full", c) for c in extra}
        controls = set((inp / "analysis" / "as_deployed_targeted_controls.txt").read_text().split())
        index = {h: i for i, h in enumerate(hosts)}
        targeted = {}
        for c, v in twin.items():
            tc, tv = load_release(inp, "remediation_targeted", c), load_release(inp, "remediation_targeted", v)
            M = V[v].copy()
            n_ctrl = ctrl_diff = twin_diff = n_aff = aff_diff = 0
            for h, r in tc.items():
                i = index.get(h)
                if i is None:
                    continue
                row = np.array(r["scores"], dtype=np.int16)
                twin_diff += int(not (np.array(tv[h]["scores"], dtype=np.int16) == V[v][i]).all())
                if h in controls:
                    n_ctrl += 1
                    ctrl_diff += int(not (row == V[v][i]).all())
                else:
                    n_aff += 1
                    aff_diff += int(not (row == V[v][i]).all())
                M[i] = row
            targeted[c] = {"controls": n_ctrl, "controls_differing": ctrl_diff, "affected_sites": n_aff,
                           "affected_vectors_differing": aff_diff, "twin_rerun_differing_from_main": twin_diff}
            if ctrl_diff or twin_diff:
                raise SystemExit(f"{c}: {ctrl_diff} control vectors differ from {v}, {twin_diff} twin reruns differ")
            V[c] = M
        result["as_deployed_targeted"] = targeted
        result["checks_as_deployed"] = checks(inp, {c: V[c] for c in extra}, hosts, sens)
        mods = {**{c: replay[c] for c in deployed if c in replay}, **sens}
        seq = {}
        for c_old, c_new in zip(deployed, deployed[1:]):
            So, Sn = V[c_old], V[c_new]
            p = {"vectors_differ_sites": int((So != Sn).any(1).sum())}
            units = []
            for T in TARGETS:
                r = compare(So, Sn, T, SPACES["all512"], strata, hosts, keep_units=True)
                m = r.pop("_masks")
                units += r.pop("_units")
                r["weighted_any_invalid_all_sites"] = population(m["any_invalid"] & in_frame, in_frame, strata)
                r["weighted_any_invalid_eligible"] = population(m["any_invalid"] & in_frame, m["elig"] & in_frame, strata)
                r["R3_scanner_guided"] = scanner_guided(So, Sn, [mods[c_old][h]["mods"] for h in hosts], T)
                p[f"all512_T{T}"] = r
            seq[f"{c_old}->{c_new}"] = p
            with gzip.open(unit_dir / f"as_deployed_{c_old}_to_{c_new}.jsonl.gz", "wt") as f:
                for u in units:
                    if u["category"] != "identical":
                        f.write(json.dumps(u) + "\n")
        result["as_deployed_pairs"] = seq
        # does a plan made under 1.5.0 as deployed fail under 1.5.1 and work again under 1.5.3?
        flip = {}
        for T in TARGETS:
            _, k0, fam0 = families(V["1.5.0-jsdom27.0.1"], T, SPACES["all512"])
            elig = (V["1.5.0-jsdom27.0.1"][:, 0] < T) & (k0 < INF)
            bad1 = fam0 & ~(V["1.5.1-jsdom27.3.0"] >= T)
            ok3 = fam0 & (V["1.5.3"] >= T)
            flip[f"T{T}"] = {"units_with_plan_failing_under_1.5.1": int((elig & bad1.any(1)).sum()),
                             "of_which_every_such_plan_valid_again_under_1.5.3":
                                 int((elig & bad1.any(1) & ~(bad1 & ~ok3).any(1)).sum())}
        result["as_deployed_flip"] = flip
    else:
        print("as-deployed analysis waits for 1.4.8 to 1.5.3 and remediation_targeted/", flush=True)

    # exploratory (D15): margins on the uncurved score, where the scorer decides both the B and A
    # boundaries and whether extra credit counts at all (remediate.mjs --with-uncurved)
    margins = {}
    for v in have:
        d = inp / "remediation_uncurved" / v
        if not d.is_dir() or len(list(d.glob("*.meta.json"))) < 53:
            continue
        rows = load_release(inp, "remediation_uncurved", v)
        U = np.array([rows[h]["uncurved"] for h in hosts], dtype=np.int16)
        if not (np.array([rows[h]["scores"] for h in hosts], dtype=np.int16) == V[v]).all():
            raise SystemExit(f"{v}: remediation_uncurved scores differ from remediation_full")
        mv = {}
        for T in TARGETS:
            _, k, fam = families(V[v], T, SPACES["all512"])
            elig = (V[v][:, 0] < T) & (k < INF)
            sel = fam & elig[:, None]
            gate = 90 if T == 100 else T
            um = (U - gate)[sel]
            shown = (V[v] - T)[sel]
            # a plan survives a p-point penalty when its uncurved score stays at or above the gate
            # and, for A+, its score stays at or above 100
            robust = (U - gate >= 5) & ((V[v] - T >= 5) if T == 100 else True)
            mv[f"T{T}"] = {"optimal_plans": int(sel.sum()),
                           "uncurved_margin": dict(Counter(um.tolist())),
                           "displayed_margin": dict(Counter(shown.tolist())),
                           "plans_one_5pt_penalty_from_failing": int((sel & ~robust).sum()),
                           "units_all_plans_within_5pt": int((elig & ~(sel & robust).any(1)).sum()),
                           "eligible": int(elig.sum())}
            # the cheapest plans that keep 5 points in hand on the scale that decides the target,
            # their extra cost, and whether they survive the next release that has a full vector
            rob = (U >= gate + 5) & ((V[v] >= T + 5) if T == 100 else True)
            k_rob = np.where(rob, SIZE[None, :], INF).min(axis=1)
            fam_rob = rob & (SIZE[None, :] == k_rob[:, None])
            ok = elig & (k_rob < INF)
            mv[f"T{T}"]["margin5_plans"] = {"units": int(ok.sum()),
                                            "extra_actions": dict(Counter((k_rob - k)[ok].tolist()))}
            later = [w for w in have if vkey(w) > vkey(v)]
            if later:
                nxt = later[0]
                fails_min = elig & (fam & ~(V[nxt] >= T)).any(1)
                fails_rob = ok & (fam_rob & ~(V[nxt] >= T)).any(1)
                mv[f"T{T}"]["margin5_plans"].update({
                    "next_release": nxt, "units_minimum_plan_fails": int(fails_min.sum()),
                    "units_margin_plan_fails": int(fails_rob.sum()),
                    "units_minimum_fails_margin_survives": int((fails_min & ok & ~fails_rob).sum())})
        margins[v] = mv
    result["uncurved_margins"] = margins

    if not a.no_age and len(have) >= 2:
        dates = {r["release"]: r["changelog_date"] for r in csv.DictReader(open(LEDGER))}
        rows = []
        for i, v_old in enumerate(have):
            for v_new in have[i + 1:]:
                for T in TARGETS:
                    So, Sn = V[v_old], V[v_new]
                    _, k_o, fam_o = families(So, T, SPACES["all512"])
                    elig = (So[:, 0] < T) & (k_o < INF)
                    inv = fam_o & ~(Sn >= T)
                    n_opt, n_inv = fam_o.sum(1), inv.sum(1)
                    any_inv = elig & (n_inv > 0)
                    e = np.where(elig)[0]
                    w = population(any_inv & in_frame, elig & in_frame, strata)
                    rows.append({"old": v_old, "new": v_new, "target": T,
                                 "days": (np.datetime64(dates[v_new]) - np.datetime64(dates[v_old])).astype(int),
                                 "eligible": int(elig.sum()), "any_invalid": int(any_inv.sum()),
                                 "none_valid": int((elig & (n_inv == n_opt)).sum()),
                                 "plans": int(n_opt[e].sum()), "plans_invalid": int(n_inv[e].sum()),
                                 "mean_tie_aware_failure": round(float((n_inv[e] / n_opt[e]).mean()), 6),
                                 "weighted_any_invalid_pct_of_eligible": w["pct"] if w else None,
                                 "ci95": w["ci95"] if w else None})
        with open(out / "plan_age.csv", "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
        result["plan_age_rows"] = len(rows)
        # a plan can fail at an intermediate release and work again later: count both
        ever = {}
        for v_old in have[:-1]:
            later = have[have.index(v_old) + 1:]
            for T in TARGETS:
                _, k_o, fam_o = families(V[v_old], T, SPACES["all512"])
                elig = (V[v_old][:, 0] < T) & (k_o < INF)
                fail_any = np.zeros_like(fam_o)
                for v_new in later:
                    fail_any |= fam_o & ~(V[v_new] >= T)
                fail_end = fam_o & ~(V[later[-1]] >= T)
                ever[f"{v_old}_T{T}"] = {
                    "eligible": int(elig.sum()),
                    "units_failing_at_some_later_release": int((elig & fail_any.any(1)).sum()),
                    "units_failing_at_last_release": int((elig & fail_end.any(1)).sum()),
                    "units_failing_meanwhile_but_valid_at_last": int((elig & fail_any.any(1) & ~fail_end.any(1)).sum()),
                    "weighted_failing_at_some_later_release_pct_of_eligible":
                        population(elig & fail_any.any(1) & in_frame, elig & in_frame, strata),
                    "weighted_failing_at_last_release_pct_of_eligible":
                        population(elig & fail_end.any(1) & in_frame, elig & in_frame, strata)}
        result["plan_age_ever_failed"] = ever

    (out / "plan_validity.json").write_text(json.dumps(result, indent=1, default=int))
    print(json.dumps(result["checks"], indent=1))


if __name__ == "__main__":
    main()
