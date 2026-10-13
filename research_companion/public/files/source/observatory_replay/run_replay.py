#!/usr/bin/env python3
"""Run replay_all.mjs or remediate.mjs over every (release, shard) pair, one Node process per pair.

One process per shard bounds memory: releases up to 1.5.2 leak one jsdom window per scan. A pair
whose output already exists is skipped, so the run can be resumed; failures are listed at the end
and the exit status is non-zero if any remain.

jsdom 27 (releases 1.4.9 to 1.5.2) also keeps about 15 MB per site after its window is closed, so a
whole shard of about 300 sites exceeds a 4 GB heap. With --chunk N each shard is scored N sites per
process and the chunk outputs are merged into the usual per-shard file, in shard order.

  python3 run_replay.py --in outputs/observatory_tranco_2026-09-27 --mode replay [--versions all] [--jobs 7]
  python3 run_replay.py --in ... --mode remediate --versions 1.3.8,1.4.0,...
  python3 run_replay.py --in ... --mode remediate --max-size 9 --out-sub remediation_full --versions ...
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path(os.environ.get("OBS_PKG_DIR", Path.home() / ".cache/sr_surrogate/observatory_pkgs"))
NODE = Path.home() / ".nvm/versions/node/v24.21.0/bin/node"


def all_versions() -> list[str]:
    # plain release numbers only; sensitivity variants such as 1.4.9-jsdom26.1.0 are run by hand
    return sorted((p.name for p in BASE.iterdir() if re.fullmatch(r"\d+\.\d+\.\d+", p.name)),
                  key=lambda v: tuple(int(x) for x in v.split(".")))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--mode", choices=["replay", "remediate"], required=True)
    ap.add_argument("--versions", default="all")
    ap.add_argument("--jobs", type=int, default=7)
    ap.add_argument("--heap-mb", type=int, default=6144)
    ap.add_argument("--hosts", help="remediate only: restrict to the hosts listed in this file")
    ap.add_argument("--max-size", type=int, help="remediate only: largest action subset (default 4)")
    ap.add_argument("--out-sub", help="output directory under --in (default replay or remediation)")
    ap.add_argument("--with-uncurved", action="store_true", help="remediate only: keep uncurved scores too")
    ap.add_argument("--chunk", type=int, help="remediate only: score at most this many sites per process")
    ap.add_argument("--csp", help="remediate only: value of the CSP action (default: the registered value)")
    a = ap.parse_args()
    inp = Path(a.inp)
    versions = all_versions() if a.versions == "all" else a.versions.split(",")
    shards = sorted(p.name for p in (inp / "shards").glob("*.jsonl.gz"))
    script = HERE / ("replay_all.mjs" if a.mode == "replay" else "remediate.mjs")
    outroot = inp / (a.out_sub or ("replay" if a.mode == "replay" else "remediation"))
    todo = [(v, s) for v in versions for s in shards
            if not (outroot / v / s.replace(".jsonl.gz", ".meta.json")).exists()]
    print(f"{len(todo)} (release, shard) jobs, {len(versions)} releases x {len(shards)} shards", flush=True)
    logdir = outroot / "logs"
    logdir.mkdir(parents=True, exist_ok=True)

    def command(v, s, extra=()):
        cmd = [str(NODE), f"--max-old-space-size={a.heap_mb}", str(script),
               "--version", v, "--in", str(inp), "--shard", s, *extra]
        if a.hosts:
            cmd += ["--hosts", str(Path(a.hosts).resolve())]
        if a.max_size:
            cmd += ["--max-size", str(a.max_size)]
        if a.with_uncurved:
            cmd += ["--with-uncurved"]
        if a.csp:
            cmd += ["--csp", a.csp]
        return cmd

    def run(job):
        v, s = job
        log = logdir / f"{v}__{s}.log"
        if a.chunk and a.mode == "remediate":
            return v, s, run_chunked(v, s, log)
        cmd = command(v, s)
        if a.out_sub:
            cmd += ["--out-sub", a.out_sub] if a.mode == "remediate" else ["--out-dir", str(outroot)]
        with open(log, "w") as fh:
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
        # jsdom prints whole stylesheets on CSS parse errors; keep the log, compressed
        subprocess.run(["gzip", "-9", "-f", str(log)])
        return v, s, rc

    def run_chunked(v, s, log):
        stem = s.replace(".jsonl.gz", "")
        hosts = [r["host"] for r in map(json.loads, gzip.open(inp / "shards" / s, "rt")) if r.get("live")]
        if a.hosts:
            keep = set(Path(a.hosts).read_text().split())
            hosts = [h for h in hosts if h in keep]
        sub = f"{a.out_sub or 'remediation'}/_chunks"
        parts, metas = [], []
        rc = 0                                   # a shard can hold no scored site at all
        with open(log, "w") as fh, tempfile.TemporaryDirectory() as tmp:
            for i in range(0, len(hosts), a.chunk):
                hf = Path(tmp) / f"hosts_{i}.txt"
                hf.write_text("\n".join(hosts[i:i + a.chunk]) + "\n")
                name = f"{stem}__c{i // a.chunk:03d}"
                cmd = command(v, s, ["--out-sub", sub, "--out-name", name])
                if a.hosts:                      # the chunk's own list replaces the global one
                    i_h = cmd.index("--hosts")
                    cmd[i_h + 1] = str(hf)
                else:
                    cmd += ["--hosts", str(hf)]
                rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
                if rc != 0:
                    break
                parts.append(inp / sub / v / f"{name}.jsonl.gz")
                metas.append(json.loads((inp / sub / v / f"{name}.meta.json").read_text()))
        subprocess.run(["gzip", "-9", "-f", str(log)])
        if rc != 0:
            return rc
        lines = [line for f in parts for line in gzip.open(f, "rt") if line.strip()]
        dest = outroot / v
        dest.mkdir(parents=True, exist_ok=True)
        with gzip.open(dest / f"{stem}.jsonl.gz", "wt") as f:
            f.writelines(lines)
        meta = {**metas[0], "n_sites": sum(m["n_sites"] for m in metas),
                "seconds": round(sum(m["seconds"] for m in metas), 3), "chunks": len(metas)} if metas else \
            {"version": v, "memoised": True, "n_sites": 0, "max_size": a.max_size or 4, "seconds": 0.0, "chunks": 0}
        (dest / f"{stem}.meta.json").write_text(json.dumps(meta, indent=1))
        for f in parts:
            f.unlink()
            f.with_name(f.name.replace(".jsonl.gz", ".meta.json")).unlink()
        return 0

    failed = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for i, (v, s, rc) in enumerate(ex.map(run, todo), 1):
            if rc != 0:
                failed.append((v, s, rc))
            if i % 25 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} done, {len(failed)} failed", flush=True)
    for f in failed:
        print("FAILED", *f)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
