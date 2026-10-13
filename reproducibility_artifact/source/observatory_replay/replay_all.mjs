// Score every stored input under one Observatory release, with that release's own scan().
//
// The release's retriever module is swapped for stub_retriever.mjs through a Node module hook, so
// scan() runs unmodified and scores the stored input instead of fetching. Releases up to 1.3.8
// call retrieve(hostname) and later ones retrieve(site); the stub ignores the argument either way.
// Reference data (HSTS preload list, TLD list) is the shared copy install_versions.sh put in every
// release.
//
// For each site the output keeps the score, the grade, each test's outcome and score modifier, and
// the uncurved score (100 plus the negative modifiers), which decides bonus eligibility.
//
//   node replay_all.mjs --version 1.7.1 --in outputs/observatory_tranco_2026-09-27 [--shard FILE] [--out-dir ...]
//
// With --shard, only that shard is scored and the output goes to replay/<version>/<shard>. Releases
// up to 1.5.2 never close the jsdom window their SRI test opens, so memory grows with every scan;
// run_replay.py therefore scores one shard per process.
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { registerHooks } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

import { unpack } from "./input_codec.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.OBS_PKG_DIR ?? path.join(process.env.HOME, ".cache/sr_surrogate/observatory_pkgs");
const STUB = pathToFileURL(path.join(HERE, "stub_retriever.mjs")).href;

registerHooks({
  resolve(specifier, context, nextResolve) {
    const r = nextResolve(specifier, context);
    if (r.url.includes("/@mdn/mdn-http-observatory/src/retriever/retriever.js")) {
      return { ...r, url: STUB, shortCircuit: true };
    }
    return r;
  },
});

const a = process.argv.slice(2);
const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const version = get("--version");
const inDir = get("--in");
const outDir = get("--out-dir", path.join(inDir, "replay"));
const onlyShard = get("--shard");
// --hosts restricts scoring to listed hosts (sensitivity runs); --out-name names the output file
const onlyHosts = get("--hosts") ? new Set(fs.readFileSync(get("--hosts"), "utf8").split(/\r?\n/).filter(Boolean)) : null;
const outName = get("--out-name");

const ROOT = path.join(BASE, version, "node_modules");
const SRC = path.join(ROOT, "@mdn/mdn-http-observatory/src");
const { scan } = await import(pathToFileURL(path.join(SRC, "scanner/index.js")).href);
const { ALGORITHM_VERSION } = await import(pathToFileURL(path.join(SRC, "constants.js")).href);
// headers are rebuilt with the 1.7.1 axios the input was collected with; every release reads them
// through Object.entries or .get(), which that class supports
const { AxiosHeaders } = await import(
  pathToFileURL(path.join(BASE, "1.7.1/node_modules/axios/index.js")).href);

const errText = (e) => `${e?.constructor?.name ?? "Error"}: ${e?.message ?? e}`;

function outcome(result) {
  const tests = {}, mods = {};
  let uncurved = 100, extra = 0;
  for (const [name, t] of Object.entries(result.tests ?? {})) {
    tests[name] = t?.result ?? null;
    const m = typeof t?.scoreModifier === "number" ? t.scoreModifier : 0;
    mods[name] = m;
    if (m < 0) uncurved += m; else extra += m;
  }
  return { score: result.scan.score, grade: result.scan.grade, uncurved, extra, tests, mods };
}

/** Score one packed input under this release. */
export async function scoreInput(packed) {
  globalThis.__OBS_STORED_INPUT__ = unpack(packed, { AxiosHeaders });
  const site = { hostname: packed.site.hostname, port: packed.site.port ?? undefined,
                 path: packed.site.path ?? undefined };
  try {
    return { status: "ok", ...outcome(await scan(site)) };
  } catch (e) {
    const msg = errText(e);
    // the scanner's own refusal of a down site or a disallowed status is not a harness failure
    const refused = /seems to be down|unexpected HTTP status|SiteIsDown|UnexpectedStatusCode/.test(msg);
    return { status: refused ? "unscannable" : "throw", error: msg };
  } finally {
    globalThis.__OBS_STORED_INPUT__ = undefined;
  }
}

async function main() {
  const shards = onlyShard ? [onlyShard]
    : fs.readdirSync(path.join(inDir, "shards")).filter((f) => f.endsWith(".jsonl.gz")).sort();
  const dest = onlyShard ? path.join(outDir, version) : outDir;
  fs.mkdirSync(dest, { recursive: true });
  const out = [];
  const counts = {};
  const t0 = Date.now();
  let n = 0;
  for (const f of shards) {
    const lines = zlib.gunzipSync(fs.readFileSync(path.join(inDir, "shards", f))).toString("utf8").split("\n");
    for (const line of lines) {
      if (!line) continue;
      const rec = JSON.parse(line);
      if (!rec.input || (onlyHosts && !onlyHosts.has(rec.host))) continue;
      const r = await scoreInput(rec.input);
      counts[r.status] = (counts[r.status] ?? 0) + 1;
      out.push(JSON.stringify({ host: rec.host, stratum: rec.stratum, shard: f, ...r }));
      n++;
    }
  }
  const name = outName ?? (onlyShard ? onlyShard.replace(/\.jsonl\.gz$/, "") : version);
  fs.writeFileSync(path.join(dest, `${name}.jsonl.gz`), zlib.gzipSync(out.join("\n") + "\n"));
  const meta = { version, algorithm_version: ALGORITHM_VERSION, n_inputs: n, counts,
                 seconds: (Date.now() - t0) / 1000, shards: shards.length };
  fs.writeFileSync(path.join(dest, `${name}.meta.json`), JSON.stringify(meta, null, 1));
  console.log(JSON.stringify(meta));
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main();
