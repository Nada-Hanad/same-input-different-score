// Minimum header-action count to reach a target score, for every site, under one release.
//
// An action changes the stored input the way a site operator would, and the release's own scan()
// scores the changed input, so the link from action to score is the scoring code itself. Every
// subset of the nine actions of size 0 to 4 (256 subsets) is scored once per site and the whole
// score vector is kept, so any target can be read off afterwards (70, 90 and 100 are
// pre-registered). Redirection and SRI cannot be fixed by a header and are not modelled, so counts
// are upper bounds.
//
// Page parsing is memoised per site (memo_jsdom.mjs, memo_html_parser.mjs) because no action
// touches the body or Content-Type. The memo is checked two ways, both outside this process:
// every site's empty-subset score must equal replay_all.mjs's unmemoised score, and a run with
// --no-memo over a sample must reproduce the full score vectors (check_remediation_memo.py).
//
// --max-size 9 scores all 512 subsets instead (deviation D13, plan-validity analysis). Subsets keep
// the same order, so the first 256 entries of such a vector are the registered depth-four vector;
// --out-sub writes it under another directory so the registered outputs stay untouched.
//
//   node remediate.mjs --version 1.7.0 --in outputs/observatory_tranco_2026-09-27 [--limit N] [--no-memo] [--hosts file]
//                      [--max-size 9 --out-sub remediation_full]
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { registerHooks } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const MEMO_JSDOM = pathToFileURL(path.join(HERE, "memo_jsdom.mjs")).href;
const MEMO_HTML = pathToFileURL(path.join(HERE, "memo_html_parser.mjs")).href;
const PKG = "/@mdn/mdn-http-observatory/src/";

const noMemo = process.argv.includes("--no-memo");
registerHooks({
  resolve(specifier, context, nextResolve) {
    const r = nextResolve(specifier, context);
    if (noMemo) return r;
    const fromRelease = context.parentURL?.includes(PKG);
    if (fromRelease && specifier === "jsdom") {
      // jsdom resolves as CommonJS; the stand-in is an ES module and must be declared as one
      return { url: `${MEMO_JSDOM}?real=${encodeURIComponent(r.url)}`, format: "module", shortCircuit: true };
    }
    if (r.url.includes(`${PKG}utils/html-parser.js`) && !r.url.includes("?unmemoised")) {
      return { url: `${MEMO_HTML}?real=${encodeURIComponent(r.url)}`, format: "module", shortCircuit: true };
    }
    return r;
  },
});

const a = process.argv.slice(2);
const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const version = get("--version");
const inDir = get("--in");
const limit = get("--limit") ? Number(get("--limit")) : Infinity;
const onlyHosts = get("--hosts") ? new Set(fs.readFileSync(get("--hosts"), "utf8").split(/\r?\n/).filter(Boolean)) : null;
const onlyShard = get("--shard");
const outName = get("--out-name", onlyShard ? onlyShard.replace(/\.jsonl\.gz$/, "") : version);
const maxSize = Number(get("--max-size", 4));
const outSub = get("--out-sub", "remediation");
// --with-uncurved also keeps each subset's uncurved score (100 plus the penalties), which decides
// whether extra credit counts; exploratory (deviation D15)
const withUncurved = a.includes("--with-uncurved");
const { scoreInput } = await import("./replay_all.mjs");

// --csp replaces the CSP action's value (sensitivity of the plan model to the chosen value, D20)
const CSP_VALUE = get("--csp", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
export const ACTIONS = [
  ["csp", "content-security-policy", CSP_VALUE],
  ["hsts", "strict-transport-security", "max-age=63072000; includeSubDomains; preload"],
  ["xfo", "x-frame-options", "DENY"],
  ["xcto", "x-content-type-options", "nosniff"],
  ["referrer", "referrer-policy", "no-referrer"],
  ["corp", "cross-origin-resource-policy", "same-origin"],
  ["coop", "cross-origin-opener-policy", "same-origin"],
  ["coep", "cross-origin-embedder-policy", "require-corp"],
  ["cookies", null, null],
];

/** Subsets of action indices of size 0..maxSize, in a fixed order (by size, then lexicographic). */
export const SUBSETS = (() => {
  const out = [[]];
  const rec = (start, cur, k) => {
    if (cur.length === k) { out.push(cur.slice()); return; }
    for (let i = start; i < ACTIONS.length; i++) { cur.push(i); rec(i + 1, cur, k); cur.pop(); }
  };
  for (let k = 1; k <= maxSize; k++) rec(0, [], k);
  return out;
})();

function applyActions(packed, subset) {
  if (subset.length === 0) return packed;
  const key = packed.responses.autoIs ?? "auto";
  const resp = { ...packed.responses[key], headers: { ...packed.responses[key].headers } };
  let session = packed.session;
  for (const i of subset) {
    const [name, header, value] = ACTIONS[i];
    if (name === "cookies") {
      // re-issuing every cookie with compliant flags is what a compliant Set-Cookie would store
      if (session?.jar?.cookies?.length) {
        session = { ...session, jar: { ...session.jar, cookies: session.jar.cookies.map((c) => ({
          ...c, secure: true, httpOnly: true, sameSite: "strict" })) } };
      }
      continue;
    }
    for (const k of Object.keys(resp.headers)) if (k.toLowerCase() === header) delete resp.headers[k];
    resp.headers[header] = value;
  }
  return { ...packed, responses: { ...packed.responses, [key]: resp }, session };
}

async function main() {
  const shards = onlyShard ? [onlyShard]
    : fs.readdirSync(path.join(inDir, "shards")).filter((f) => f.endsWith(".jsonl.gz")).sort();
  const out = [];
  let n = 0;
  const t0 = Date.now();
  for (const f of shards) {
    const lines = zlib.gunzipSync(fs.readFileSync(path.join(inDir, "shards", f))).toString("utf8").split("\n");
    for (const line of lines) {
      if (!line || n >= limit) continue;
      const rec = JSON.parse(line);
      if (!rec.live || (onlyHosts && !onlyHosts.has(rec.host))) continue;
      const scores = [];
      const uncurved = [];
      let status = "ok";
      for (const subset of SUBSETS) {
        const r = await scoreInput(applyActions(rec.input, subset));
        if (r.status !== "ok") { status = r.status; scores.push(null); uncurved.push(null); }
        else { scores.push(r.score); uncurved.push(r.uncurved); }
      }
      out.push(JSON.stringify({ host: rec.host, stratum: rec.stratum, status, scores,
                                ...(withUncurved ? { uncurved } : {}) }));
      n++;
      if (n % 1000 === 0) console.log(`${version} ${n} sites ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
  }
  const dir = onlyShard ? path.join(inDir, outSub, version) : path.join(inDir, outSub);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, `${outName}.jsonl.gz`), zlib.gzipSync(out.join("\n") + "\n"));
  const meta = { version, memoised: !noMemo, n_sites: n, subsets: SUBSETS.length, max_size: maxSize,
                 actions: ACTIONS.map((x) => x[0]), seconds: (Date.now() - t0) / 1000 };
  fs.writeFileSync(path.join(dir, `${outName}.meta.json`), JSON.stringify(meta, null, 1));
  console.log(JSON.stringify(meta));
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main();
