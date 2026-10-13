import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "../hosting";
import React, { useState, useEffect } from "react";
import {
  populationRows,
  filterPopulation,
  readableMeasurement,
  measurementTest,
  planCounts,
  percentage,
  download,
  type Research,
  type Pair,
  type Target,
} from "../model";
import {
  fmt,
  nice,
  IntervalText,
  Stat,
  Callout,
  Table,
  Bars,
  PairControl,
  TargetControl,
  Source,
} from "../components";
const liveRate = (d: Research) =>
  (100 * d.gates.live.exact_score_rate).toFixed(1);
export default function Population({ data }: { data: Research }) {
  const q = new URLSearchParams(routeSearch()),
    options = data.releases.map((x) => x.release);
  const pairDefault=data.pairs.find(p=>p.pair===q.get("pair")) ?? data.pairs.find(p=>p.old==="1.5.2")!;
  const [old, setOld] = useState(
    options.includes(q.get("from") ?? "") ? q.get("from")! : pairDefault.old,
  );
  const [next, setNext] = useState(
    options.includes(q.get("to") ?? "") ? q.get("to")! : pairDefault.new,
  );
  const metrics = Array.from(
    new Set([
      ...Object.keys(data.population.levels[old]),
      ...Object.keys(data.population.levels[next]),
    ]),
  ).sort();
  const [metric, setMetric] = useState(
    metrics.includes(q.get("metric") ?? "")
      ? q.get("metric")!
      : "outcome sri-not-implemented-and-external-scripts-not-loaded-securely",
  );
  const [search, setSearch] = useState(q.get("pop_search") ?? "");
  const [family, setFamily] = useState(q.get("pop_family") ?? "All");
  const [test, setTest] = useState(q.get("pop_test") ?? "All");
  const [sort, setSort] = useState(q.get("pop_sort") ?? "absolute");
  const [raw, setRaw] = useState(q.get("raw") === "true");
  const allRows = populationRows(data, old, next);
  const filtered = filterPopulation(allRows, search, family, test, sort);
  const tests = Array.from(
    new Set(
      allRows.filter((r) => r.family === "Test outcomes").map((r) => r.test),
    ),
  ).sort();
  const groups = Array.from(new Set(filtered.map((r) => r.test)));
  const shown = groups.flatMap((group) =>
    filtered.filter((r) => r.test === group),
  );
  useEffect(() => {
    const u = routeUrl();
    for (const [k, v] of Object.entries({
      pop_search: search,
      pop_family: family,
      pop_test: test,
      pop_sort: sort,
      raw: String(raw),
    }))
      u.searchParams.set(k, v);
    writeRoute(u);
  }, [search, family, test, sort, raw]);
  useEffect(() => {
    const u = routeUrl();
    u.searchParams.set("from", old);
    u.searchParams.set("to", next);
    u.searchParams.set("metric", metric);
    writeRoute(u);
  }, [old, next, metric]);
  const a = data.population.levels[old][metric],
    b = data.population.levels[next][metric];
  const change =
      data.population.changes[`registered: ${old} -> ${next}`]?.[metric],
    factor = metric === "mean score" ? 1 : 100;
  const estimates = [
    { v: old, z: a },
    { v: next, z: b },
  ];
  return (
    <>
      <Callout>
        <strong>Fixed website responses.</strong> These are changes in weighted
        measurements when only the scorer release changes. They do not describe
        historical changes in website configurations or establish a change in
        actual Web security.
      </Callout>
      <div className="controls">
        <label className="control">
          Baseline release
          <select value={old} onChange={(e) => setOld(e.target.value)}>
            {options.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label className="control">
          Comparison release
          <select value={next} onChange={(e) => setNext(e.target.value)}>
            {options.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label className="control wide">
          Measurement
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            {metrics.map((m) => (
              <option key={m} value={m}>
                {measurementTest(m)} · {readableMeasurement(m)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <section className="panel">
        <h3>
          {measurementTest(metric)} · {readableMeasurement(metric)}
        </h3>
        {raw && <code>{metric}</code>}
        <Bars
          label={`Weighted ${metric} under ${old} and ${next}`}
          rows={estimates
            .filter((x) => x.z)
            .map((x) => ({ label: x.v, values: [x.z[0] * factor] }))}
        />
        <table>
          <caption>
            Weighted levels {factor === 100 ? "in percent" : "in score points"}.
            Intervals are recorded stratified-bootstrap 95% intervals.
          </caption>
          <thead>
            <tr>
              <th>Release</th>
              <th>Estimate</th>
              <th>95% interval</th>
            </tr>
          </thead>
          <tbody>
            {estimates.map(({ v, z }, i) => (
              <tr key={`${v}-${i}`}>
                <th>{v}</th>
                <td>{z ? (z[0] * factor).toFixed(4) : "Not recorded"}</td>
                <td>
                  {z?.[1]
                    ? z[1].map((n) => (n * factor).toFixed(4)).join(" to ")
                    : "Not recorded"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="caption">
          Recorded measurement difference:{" "}
          {a && b ? ((b[0] - a[0]) * factor).toFixed(4) : "Not recorded"}{" "}
          {factor === 100 ? "percentage points" : "score points"}. Paired
          difference interval:{" "}
          {change?.ci95
            ? change.ci95.map((v) => (v * factor).toFixed(4)).join(" to ")
            : old === next
              ? "Same-release comparison; no release change."
              : "Not available for this selected measurement/pair; not inferred from level intervals."}
        </p>
        {(!a || !b) && (
          <Callout>
            This outcome level is not recorded for one selected release. A
            missing outcome is not silently substituted with zero.
          </Callout>
        )}
      </section>
      <section className="panel">
        <h3>Explore supported measurements</h3>
        <div className="controls">
          <label className="control wide">
            Filter measurements
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Grade, mean score, or test outcome"
            />
          </label>
          <label className="control">
            Measurement family
            <select value={family} onChange={(e) => setFamily(e.target.value)}>
              {["All", "Grade shares", "Mean score", "Test outcomes"].map(
                (f) => (
                  <option key={f}>{f}</option>
                ),
              )}
            </select>
          </label>
          <label className="control">
            Security test group
            <select value={test} onChange={(e) => setTest(e.target.value)}>
              <option>All</option>
              <option>Population summary</option>
              {tests.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="control">
            Sort measurements
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="absolute">Absolute change</option>
              <option value="signed">Signed change</option>
              <option value="name">Measurement name</option>
            </select>
          </label>
        </div>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={raw}
            onChange={(e) => setRaw(e.target.checked)}
          />
          Show exact outcome identifiers
        </label>
        <p className="caption">
          {filtered.length} measurements, grouped by security test; sorted
          within each group. Shares are percent; share differences are
          percentage points. Mean scores and their changes are score points.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Measurement</th>
                <th>{old}</th>
                <th>{next}</th>
                <th>Difference</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r, i) => (
                <React.Fragment key={r.id}>
                  {(i === 0 || shown[i - 1].test !== r.test) && (
                    <tr className="metric-group">
                      <th colSpan={4}>{r.test}</th>
                    </tr>
                  )}
                  <tr>
                    <th>
                      <button onClick={() => setMetric(r.id)}>{r.name}</button>
                      {raw && (
                        <div>
                          <code>{r.id}</code>
                        </div>
                      )}
                    </th>
                    <td>
                      {r.old === null ? "Not recorded" : r.old.toFixed(3)}
                    </td>
                    <td>
                      {r.next === null ? "Not recorded" : r.next.toFixed(3)}
                    </td>
                    <td>
                      {r.change === null ? "Not recorded" : r.change.toFixed(3)}
                    </td>
                  </tr>
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <Callout>No measurements match these filters.</Callout>
        )}
        <button
          onClick={() =>
            download("filtered-population.json", {
              baseline: old,
              comparison: next,
              filters: { search, family, test, sort },
              source: "aggregate_drift.json",
              record_units:
                "Original record shares are fractions; mean scores are points. Normalized row levels are percent and share changes are percentage points.",
              rows: filtered.map((r) => ({
                ...r,
                baseline_record: data.population.levels[old][r.id] ?? null,
                comparison_record: data.population.levels[next][r.id] ?? null,
                paired_change_record:
                  data.population.changes[`registered: ${old} -> ${next}`]?.[
                    r.id
                  ] ?? null,
              })),
            })
          }
        >
          Download filtered measurements ↓
        </button>
      </section>
      <section className="panel">
        <h3>Complete grade distribution</h3>
        <p className="caption">
          Derived for this companion from the stored website-score matrix.
          Percentages use original Tranco frame weights; counts include the
          separate legacy panel. No uncertainty intervals were generated for
          this added view.
        </p>
        <table>
          <thead>
            <tr>
              <th>Grade</th>
              <th>{old} count</th>
              <th>{old} weighted %</th>
              <th>{next} count</th>
              <th>{next} weighted %</th>
            </tr>
          </thead>
          <tbody>
            {[
              "F",
              "D-",
              "D",
              "D+",
              "C-",
              "C",
              "C+",
              "B-",
              "B",
              "B+",
              "A-",
              "A",
              "A+",
            ].map((g) => (
              <tr key={g}>
                <th scope="row">{g}</th>
                <td>{fmt(data.grade_distributions[old].counts[g] ?? 0)}</td>
                <td>
                  {(
                    (data.grade_distributions[old].weighted_fraction[g] ?? 0) *
                    100
                  ).toFixed(3)}
                </td>
                <td>{fmt(data.grade_distributions[next].counts[g] ?? 0)}</td>
                <td>
                  {(
                    (data.grade_distributions[next].weighted_fraction[g] ?? 0) *
                    100
                  ).toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="caption">
        {fmt(data.population.sites)} scored Tranco websites, legacy panel
        excluded. {data.population.note}. Most outcome-level intervals were not
        produced by the original analysis. Population analysis was exploratory
        under D20.
      </p>
      <Source names={["aggregate_drift.json", "aggregate_drift.py"]} />
    </>
  );
}
