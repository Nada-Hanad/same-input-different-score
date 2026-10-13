import {opaqueOrigin} from "./hosting";
export type Target = "B" | "A" | "A+";
export type Interval = { pct: number; ci95: [number, number] };
export type Plan = {
  restoration?: {
    any_subset_restores: number;
    no_subset_reaches: number;
    failing_websites: number;
  };
  scope?: string;
  n?: number;
  eligible: number | null;
  note?: string;
  fate: Record<string, number>;
  category?: Record<string, number>;
  any_invalid_base_unchanged?: number;
  additional_effort_min?: Record<string, number>;
  additional_effort_max?: Record<string, number>;
  action_count_transitions?: Record<string, number>;
  plans_total?: number;
  plans_invalid?: number;
  weighted_any_invalid_all_sites?: Interval;
  weighted_any_invalid_eligible?: Interval;
  optimal_plan_slack?: Record<string, number>;
  invalid_plan_slack?: Record<string, number>;
};
export type Pair = {
  exposure: {
    recorded: number;
    registered: number | null;
    recorded_status: string;
    corrected: number | null;
    corrected_ci95: [number, number] | null;
    corrected_weighted: Interval | null;
    correction_status: string | null;
  };
  pair: string;
  old: string;
  new: string;
  class: string;
  n_both_ok: number;
  E: number;
  T: number;
  S: number;
  G: number;
  n_T_outside_E: number;
  tests_changed: Record<string, number>;
  delta: Record<string, number>;
  grade_moves: Record<string, number>;
  weighted_top1M: Record<string, Interval>;
  algorithm_old: number;
  algorithm_new: number;
  release: {
    changelog_date: string;
    scoring_change_from_diff: string;
    changelog_scoring_relevant: string;
    jsdom_installed_for_replay: string;
    htmlparser2_installed_for_replay: string;
  };
  plans: Record<Target, Plan>;
  exposure_note: string;
  evidence: string[];
};
export type Evidence = {
  result_kind?: string;
  verification_method?: string;
  qualification?: string;
  figure_download_url?: string;
  script_download_url?: string | null;
  access_category:
    | "Included and downloadable"
    | "Reproducible using public fixtures"
    | "Restricted original data required";
  included_dataset: string;
  included_dataset_url: string;
  id: string;
  rq: string;
  manuscript_location: string;
  claim: string;
  source: string;
  source_sha256: string | null;
  script: string;
  script_sha256: string;
  figure: string | null;
  command: string;
  restricted_inputs: boolean;
  configuration: string;
  evidence_level: string;
};
export type Audit = {
  baseline: string;
  candidate: string;
  algorithm_version: { baseline: number[]; candidate: number[] };
  sites_compared: number;
  test_outcome_changed: number;
  score_changed: number;
  grade_changed: number;
  plan_vectors_differ_sites: number;
  tests_changed: Record<string, number>;
  plans: Record<Target, Plan>;
  source: string;
  kind: string;
  weighted_score_changed: Interval;
  weighted_grade_changed: Interval;
};
export type Research = {
  actions: {
    id: string;
    label: string;
    header: string | null;
    value: string | null;
    modifies: string;
  }[];
  synthetic_replay: SyntheticReplay;
  synthetic_flooring: {original:{old:FixtureResult;new:FixtureResult};plan:SyntheticReplay["plan"];construction:string};
  a_aplus_identity: {
    pairs: {
      pair: string;
      A: number;
      "A+": number;
      same_websites: boolean;
      intersection: number;
    }[];
    union: {
      A: number;
      "A+": number;
      same_websites: boolean;
      intersection: number;
    };
    limitations: string;
  };
  schema_version: number;
  title: string;
  subtitle: string;
  summary: {
    releases: number;
    pairs: number;
    scored: number;
    collected: number;
    comparisons: number;
    scores: number;
    grades: number;
    unique_failing: Record<Target, number>;
    unchanged_algorithm_scores: number;
    unchanged_algorithm_grades: number;
    unchanged_algorithm_failing: Record<Target, number>;
    full_plan_pairs: number;
    sampled_plan_pairs: number;
  };
  releases: {
    release: string;
    changelog_date: string;
    algorithm_version: string;
  }[];
  pairs: Pair[];
  mechanisms: {
    pair: string;
    class: string;
    test: string;
    sites: number;
    explained: boolean;
    changed_in_closure: string[];
  }[];
  population: {
    sites: number;
    note: string;
    levels: Record<string, Record<string, [number, [number, number] | null]>>;
    changes: Record<
      string,
      Record<
        string,
        { change: number; ci95: [number, number] | null; sites_changed: number }
      >
    >;
  };
  audits: Audit[];
  manifest: Evidence[];
  missing: string[];
  gates: {
    storage: { exact: number; of: number; pass: boolean };
    live: {
      exact_score: number;
      both_scored: number;
      exact_score_rate: number;
      pass: boolean;
    };
    compatibility: {
      pass_as_worded: boolean;
      pass_on_inputs_scored_at_collection: boolean;
    };
    memo: Record<
      string,
      {
        sampled: number;
        rerun_ok: number;
        identical_vectors: number;
        process_failures: number;
      }
    >;
  };
  grade_distributions: Record<
    string,
    {
      counts: Record<string, number>;
      weighted_fraction: Record<string, number>;
      ci95: null;
      note: string;
    }
  >;
  parser_mechanism_counts: Record<Target, Record<string, number>>;
  margins: Record<
    string,
    Record<
      string,
      {
        optimal_plans: number;
        uncurved_margin: Record<string, number>;
        displayed_margin: Record<string, number>;
      }
    >
  >;
};
export const pages = [
  "Overview",
  "Release Explorer",
  "Remediation Plans",
  "Mechanisms",
  "Population Effects",
  "Release-Impact Audit",
  "Artifact",
] as const;
export function versionKey(v: string) {
  return v.split(".").map(Number);
}
export function compareVersions(a: string, b: string) {
  const x = versionKey(a),
    y = versionKey(b);
  return x[0] - y[0] || x[1] - y[1] || x[2] - y[2];
}
export function percentage(n: number | null | undefined, d: number | null | undefined) {
  return n != null && d != null && d > 0 ? (100 * n) / d : null;
}
export function planCounts(p: Plan) {
  return {
    every: p.fate.every_fails ?? 0,
    some: p.fate.some_fail ?? 0,
    none:
      p.fate.none_fail ??
      (p.eligible === null
        ? null
        : p.eligible - (p.fate.every_fails ?? 0) - (p.fate.some_fail ?? 0)),
  };
}
export function selectState(data: Research, search: string) {
  const q = new URLSearchParams(search);
  const page = pages.find((p) => p === q.get("view")) ?? "Overview";
  const pair =
    data.pairs.find((p) => p.pair === q.get("pair")) ??
    data.pairs.find((p) => p.old === "1.5.2")!;
  const target: Target = ["B", "A", "A+"].includes(q.get("target") ?? "")
    ? (q.get("target") as Target)
    : "B";
  return { page, pair, target };
}
export function download(name: string, value: unknown) {
  if(opaqueOrigin()){window.dispatchEvent(new CustomEvent("artifact-export",{detail:{name,text:JSON.stringify(value,null,2)}}));return;}
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export type Coverage = "all" | "full" | "sampled" | "failures";
export function filterPlanPairs(
  pairs: Pair[],
  target: Target,
  coverage: Coverage,
) {
  return pairs.filter(
    (p) =>
      coverage === "all" ||
      (coverage === "full" && p.plans[target].scope === "full-corpus") ||
      (coverage === "sampled" && p.plans[target].scope === "control-sample") ||
      (coverage === "failures" &&
        planCounts(p.plans[target]).every + planCounts(p.plans[target]).some >
          0),
  );
}
export type FixtureResult = {
  score: number;
  grade: string;
  uncurved: number;
  extra: number;
  algorithm_version: number;
  tests: Record<string, string>;
  mods: Record<string, number>;
};
export type SyntheticReplay = {
  kind: string;
  network_attempts: number;
  scoring_rule: { pair: string; old: FixtureResult; new: FixtureResult };
  parser: { pair: string; old: FixtureResult; new: FixtureResult };
  plan: {
    target_grade: string;
    target_score: number;
    subsets_evaluated_per_release: number;
    minimum_actions: number;
    tied_minimum_plans: {
      actions: string[];
      old: FixtureResult;
      new: FixtureResult;
    }[];
    every_tied_plan_fails: boolean;
    any_new_subset_reaches: boolean;
    maximum_new_score: number;
  };
  limitations: string;
};
export const testNames: Record<string, string> = {
  csp: "Content Security Policy",
  "content-security-policy": "Content Security Policy",
  cookies: "Cookies",
  "cross-origin-resource-sharing": "Cross-Origin Resource Sharing",
  redirection: "Redirection",
  "referrer-policy": "Referrer Policy",
  "strict-transport-security": "Strict Transport Security",
  "subresource-integrity": "Subresource Integrity",
  "x-content-type-options": "Content-Type Options",
  "x-frame-options": "Frame Options",
  "cross-origin-resource-policy": "Cross-Origin Resource Policy",
  "cross-origin-embedder-policy": "Cross-Origin Embedder Policy",
  "cross-origin-opener-policy": "Cross-Origin Opener Policy",
};
const prefixes: Record<string, string> = {
  csp: "content-security-policy",
  cookies: "cookies",
  cors: "cross-origin-resource-sharing",
  "cross-origin-resource-sharing": "cross-origin-resource-sharing",
  redirection: "redirection",
  "referrer-policy": "referrer-policy",
  hsts: "strict-transport-security",
  sri: "subresource-integrity",
  "html-not-parseable": "subresource-integrity",
  "x-content-type-options": "x-content-type-options",
  "x-frame-options": "x-frame-options",
  corp: "cross-origin-resource-policy",
  coep: "cross-origin-embedder-policy",
  coop: "cross-origin-opener-policy",
};
export function measurementFamily(m: string) {
  return m.startsWith("outcome ")
    ? "Test outcomes"
    : m === "mean score"
      ? "Mean score"
      : "Grade shares";
}
export function measurementTest(m: string) {
  if (!m.startsWith("outcome ")) return "Population summary";
  const o = m.slice(8);
  const key = Object.keys(prefixes)
    .sort((a, b) => b.length - a.length)
    .find((k) => o === k || o.startsWith(k + "-"));
  return key ? testNames[prefixes[key]] : "Other test";
}
export function readableMeasurement(m: string) {
  if (!m.startsWith("outcome ")) return m === "mean score" ? "Mean score" : m;
  const o = m.slice(8);
  const prefix = Object.keys(prefixes)
    .sort((a, b) => b.length - a.length)
    .find((k) => o === k || o.startsWith(k + "-"));
  const text = (
    prefix && prefix !== "html-not-parseable" ? o.slice(prefix.length + 1) : o
  ).replaceAll("-", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
export type PopulationRow = {
  id: string;
  name: string;
  family: string;
  test: string;
  old: number | null;
  next: number | null;
  change: number | null;
  unit: string;
};
export function populationRows(
  data: Research,
  old: string,
  next: string,
): PopulationRow[] {
  return Array.from(
    new Set([
      ...Object.keys(data.population.levels[old]),
      ...Object.keys(data.population.levels[next]),
    ]),
  ).map((id) => {
    const a = data.population.levels[old][id],
      b = data.population.levels[next][id],
      factor = id === "mean score" ? 1 : 100;
    return {
      id,
      name: readableMeasurement(id),
      family: measurementFamily(id),
      test: measurementTest(id),
      old: a ? a[0] * factor : null,
      next: b ? b[0] * factor : null,
      change: a && b ? (b[0] - a[0]) * factor : null,
      unit:
        id === "mean score"
          ? "score points"
          : "percent (levels); percentage points (change)",
    };
  });
}
export function filterPopulation(
  rows: PopulationRow[],
  query: string,
  family: string,
  test: string,
  sort: string,
) {
  return rows
    .filter(
      (r) =>
        (family === "All" || r.family === family) &&
        (test === "All" || r.test === test) &&
        `${r.id} ${r.name} ${r.test}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    )
    .sort((a, b) =>
      sort === "name"
        ? a.test.localeCompare(b.test) || a.name.localeCompare(b.name)
        : a.change === null
          ? b.change === null
            ? a.id.localeCompare(b.id)
            : 1
          : b.change === null
            ? -1
            : sort === "signed"
              ? b.change - a.change
              : Math.abs(b.change) - Math.abs(a.change),
    );
}
