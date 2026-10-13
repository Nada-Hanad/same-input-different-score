import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "../hosting";
import React, { useState, useEffect } from "react";
import {
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
export default function Audits({ data }: { data: Research }) {
  const [index, setIndex] = useState(0);
  const a = data.audits[index];
  return (
    <>
      <section className="panel">
        <h3>Compare precomputed audits</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Report</th>
                <th>Analysis type</th>
                <th>Test outcomes</th>
                <th>Scores</th>
                <th>Grades</th>
                <th>Any failing B plan</th>
              </tr>
            </thead>
            <tbody>
              {data.audits.map((x, i) => (
                <tr key={x.candidate}>
                  <th>
                    <button onClick={() => setIndex(i)}>
                      {x.baseline} → {x.candidate}
                    </button>
                  </th>
                  <td>{x.kind}</td>
                  <td>{x.test_outcome_changed}</td>
                  <td>{x.score_changed}</td>
                  <td>{x.grade_changed}</td>
                  <td>
                    {planCounts(x.plans.B).every + planCounts(x.plans.B).some}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <label className="control wide">
        Precomputed release-impact report
        <select
          value={index}
          onChange={(e) => setIndex(Number(e.target.value))}
        >
          {data.audits.map((x, i) => (
            <option value={i} key={x.candidate}>
              {x.baseline} → {x.candidate} · {x.kind}
            </option>
          ))}
        </select>
      </label>
      <div className="pair-title">
        <h2>
          {a.baseline} → {a.candidate}
        </h2>
        <span className="badge">{a.kind}</span>
      </div>
      <div className="stats">
        <Stat value={a.sites_compared} label="reference-corpus websites" />
        <Stat value={a.test_outcome_changed} label="changed test outcomes" />
        <Stat value={a.score_changed} label="changed scores" />
        <Stat value={a.grade_changed} label="changed grades" />
      </div>
      <section className="panel">
        <h3>Modeled plan changes</h3>
        <table>
          <caption>Previously sufficient minimum-action plans</caption>
          <thead>
            <tr>
              <th>Target</th>
              <th>Eligible</th>
              <th>Every fails</th>
              <th>Some fail</th>
              <th>Failing, original score unchanged</th>
            </tr>
          </thead>
          <tbody>
            {(["B", "A", "A+"] as Target[]).map((t) => {
              const p = a.plans[t],
                c = planCounts(p);
              return (
                <tr key={t}>
                  <th>{t}</th>
                  <td>{fmt(p.eligible ?? 0)}</td>
                  <td>{c.every}</td>
                  <td>{c.some}</td>
                  <td>{p.any_invalid_base_unchanged}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p>
          Reported algorithm version: {a.algorithm_version.baseline.join(", ")}{" "}
          → {a.algorithm_version.candidate.join(", ")}. Websites with changed
          modeled score vectors: {a.plan_vectors_differ_sites}.
        </p>
        <p>
          Weighted score-change share:{" "}
          <IntervalText value={a.weighted_score_changed} />. Weighted
          grade-change share: <IntervalText value={a.weighted_grade_changed} />.
        </p>
        <div className="buttons">
          <button
            className="primary"
            onClick={() => download(`${a.baseline}-vs-${a.candidate}.json`, a)}
          >
            Export report JSON ↓
          </button>
          <button onClick={() => window.print()}>Print readable report</button>
        </div>
      </section>
      <Callout>
        <strong>An observed zero has a coverage boundary.</strong> No observed
        change on these stored responses does not prove that a candidate has no
        effect elsewhere. Collection failures, unobserved response types, the
        European vantage point, and the nine-action model limit the audit.
        Candidate results apply to the recorded commit and dependency
        configuration.
      </Callout>
      <section className="panel">
        <h3>Local candidate auditing</h3>
        <p>
          Install and pin the candidate in an isolated environment. Replay the
          restricted reference corpus and run the 512-subset search before
          producing the report. The public interface uses precomputed results.
        </p>
        <p className="caption">
          Complete empirical auditing requires restricted stored responses,
          completed replay/plan vectors and a retained installation environment.
          This one-line shell command was exercised for the positive control
          using an isolated input view; it never writes to the original corpus.
        </p>
        <pre>
          {a.baseline === "1.6.3"
            ? 'python3.11 source/observatory_replay/audit_release.py --in "$OBS_CORPUS_COPY" --baseline 1.6.3 --candidate 1.7.0 --candidate-replay replay --candidate-plans remediation_full'
            : `python3.11 source/observatory_replay/audit_release.py --in "$OBS_CORPUS_COPY" --baseline ${a.baseline} --candidate ${a.candidate}`}
        </pre>
        <p className="caption">
          Run from reproducibility_artifact after setting OBS_CORPUS_COPY to a
          new isolated copy with the required stored vectors. A fresh candidate
          replay and 512-subset search must be completed first. Candidate
          commands are syntax-checked templates; only the stated
          positive-control analysis was rerun here.
        </p>
        <a href={resource("/docs/REPRODUCIBILITY.md")}  download>
          Download local replay instructions ↓
        </a>
      </section>
      <Source names={[a.source, "audit_release.py"]} />
    </>
  );
}
