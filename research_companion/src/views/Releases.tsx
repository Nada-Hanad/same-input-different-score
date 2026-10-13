import {classificationLabel, classificationMeaning, pairExplanation} from "../classifications";
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
export default function Releases({
  data,
  pair,
  setPair,
}: {
  data: Research;
  pair: Pair;
  setPair: (p: Pair) => void;
}) {
  const measurements = [
    {label: pair.old === "1.3.8" ? "Registered exposure" : "Recorded exposure", value: pair.exposure.recorded},
    ...(pair.exposure.corrected != null ? [{label: "Corrected parser-faithful exposure", value: pair.exposure.corrected}] : []),
    {label: "Test outcome", value: pair.T},
    {label: "Score", value: pair.S},
    {label: "Grade", value: pair.G},
  ];
  const allZero = measurements.every(row => row.value === 0);
  const hasMissing = measurements.some(row => row.value == null);
  return (
    <>
      <PairControl data={data} pair={pair} onChange={setPair} />
      <div className="pair-title">
        <h2>{nice(pair.pair)}</h2>
        <span className="badge">{classificationLabel(pair.class)}</span>
      </div>
      <p className="lead">{pairExplanation(pair)}</p>
      <p className="caption">{classificationMeaning(pair.class)}</p>
      {pair.release.scoring_change_from_diff && <details>
        <summary>Recorded implementation note</summary>
        <p>{pair.release.scoring_change_from_diff}</p>
      </details>}
      <div className="stats">
        <Stat
          value={pair.exposure.recorded}
          label={
            pair.old === "1.3.8"
              ? "registered exposure matches"
              : "recorded exposure matches"
          }
          detail={pair.exposure.recorded_status}
        />
        <Stat
          value={pair.T}
          label="changed test outcomes"
          detail="Websites with any changed test"
        />
        <Stat
          value={pair.S}
          label="changed scores"
          detail={percentage(pair.S, pair.n_both_ok) === null ? "Not recorded" : `${percentage(pair.S, pair.n_both_ok)!.toFixed(3)}% of ${fmt(pair.n_both_ok)}`}
        />
        <Stat value={pair.G} label="changed grades" />
      </div>
      {pair.exposure.corrected !== null && (
        <section className="panel">
          <h3>Registered and corrected exposure conditions</h3>
          <div className="stats">
            <Stat
              value={pair.exposure.registered ?? "Not recorded"}
              label="Registered exposure condition"
            />
            <Stat
              value={pair.exposure.corrected}
              label="Corrected parser-faithful exposure condition"
            />
            <Stat value={pair.T} label="Changed test outcomes" />
          </div>
          <p className="caption">
            {pair.exposure.correction_status} All changed outcomes are contained
            by the corrected condition. The weighted corrected exposure interval
            is recorded in the original E_unsplit diagnostic; it was omitted from the earlier companion.
          </p>
        </section>
      )}
      <Callout>
        <strong>Exposure interpretation.</strong> {pair.exposure_note}{" "}
        {pair.n_T_outside_E > 0 &&
          `${pair.n_T_outside_E} test-outcome changes fall outside the recorded exposure condition.`}
      </Callout>
      <div className="split">
        <section className="panel">
          <h3>Exposure to measured change</h3>
          {allZero || hasMissing ? <>
            {allZero && <p>All recorded measurements are zero for this pair. These are observed results, not missing data.</p>}
            <Table rows={Object.fromEntries(measurements.map(row => [row.label, row.value]))} label="Recorded exposure and changed assessment counts" />
          </> : <Bars label="Recorded exposure and changed assessment counts" rows={measurements.map(row => ({label: row.label, values: [row.value]}))} />}
          <p className="caption">
            Each count uses the same {fmt(pair.n_both_ok)} scored websites.
            Per-test counts can overlap; they must not be summed as distinct
            websites.
          </p>
        </section>
        <section className="panel">
          <h3>Weighted Tranco estimates</h3>
          <table>
            <caption>
              Recorded stratified-bootstrap 95% intervals; legacy panel excluded
            </caption>
            <thead>
              <tr>
                <th>Measurement</th>
                <th>Estimate [95% interval]</th>
              </tr>
            </thead>
            <tbody>
              {[
                [
                  "E",
                  pair.old === "1.3.8"
                    ? "Registered exposure"
                    : "Recorded exposure",
                ],
                ["T", "Test outcome"],
                ["S", "Score"],
                ["G", "Grade"],
              ].map(([k, label]) => (
                <tr key={k}>
                  <th scope="row">{label}</th>
                  <td>
                    <IntervalText value={pair.weighted_top1M[k]} />
                  </td>
                </tr>
              ))}
            </tbody>
              {pair.exposure.corrected_weighted && <tbody><tr><th>Corrected parser-faithful exposure</th><td><IntervalText value={pair.exposure.corrected_weighted} /></td></tr></tbody>}
          </table>
          <p className="caption">
            Frame-weighted estimates among scored websites in each rank stratum.
            Zero bootstrap intervals describe observed samples, not universal
            zero-effect guarantees.
          </p>
        </section>
      </div>
      <div className="split">
        <section className="panel">
          <Table
            rows={pair.tests_changed}
            label="Changed test outcomes by test"
            emptyLabel={pair.T === 0 ? "No test-outcome differences were observed on the fixed reference corpus." : "Not recorded"}
          />
        </section>
        <section className="panel">
          <Table rows={pair.delta} label="Score differences (new minus old)" emptyLabel={pair.S === 0 ? "No score differences were observed on the fixed reference corpus." : "Not recorded"} />
        </section>
      </div>
      <div className="split">
        <section className="panel">
          <h3>Release and disclosure</h3>
          <dl>
            <dt>Reported algorithm version</dt>
            <dd>
              {pair.algorithm_old} → {pair.algorithm_new} ·{" "}
              {pair.algorithm_old === pair.algorithm_new
                ? "unchanged"
                : "changed"}
            </dd>
            <dt>Changelog date</dt>
            <dd>{pair.release.changelog_date}</dd>
            <dt>Recorded changelog content</dt>
            <dd>
              {pair.release.changelog_scoring_relevant ||
                "No scoring-relevant description recorded."}
            </dd>
            <dt>Installed parser dependency</dt>
            <dd>
              {pair.release.jsdom_installed_for_replay
                ? `jsdom ${pair.release.jsdom_installed_for_replay}`
                : pair.release.htmlparser2_installed_for_replay
                  ? `htmlparser2 ${pair.release.htmlparser2_installed_for_replay}`
                  : "Not recorded"}
            </dd>
          </dl>
        </section>
        <section className="panel">
          <Table rows={pair.grade_moves} label="Observed grade transitions" emptyLabel={pair.G === 0 ? "No grade differences were observed on the fixed reference corpus." : "Not recorded"} />
        </section>
      </div>
      <Callout>
        <strong>Metric definitions.</strong> Test-outcome changes count websites
        with any changed test, not individual tests. Exposure matches count
        websites meeting an input condition. Score and grade changes compare the
        same stored responses; per-test counts can overlap.
      </Callout>
      <div className="buttons" aria-label="Explore this release pair">
        <a href={`#?view=Mechanisms&pair=${encodeURIComponent(pair.pair)}`}>Inspect mechanisms →</a>
        <a href={`#?view=Remediation%20Plans&pair=${encodeURIComponent(pair.pair)}&target=B`}>Inspect plan validity →</a>
        <a href={`#?view=Population%20Effects&pair=${encodeURIComponent(pair.pair)}&from=${pair.old}&to=${pair.new}`}>Compare population measurements →</a>
        <a href={`#?view=Release-Impact%20Audit&pair=${encodeURIComponent(pair.pair)}`}>Review candidate and control audits →</a>
        <a href={`#?view=Artifact&pair=${encodeURIComponent(pair.pair)}&search=${pair.old==='1.5.2'?'parser':'outcomes'}`}>Trace supporting evidence →</a>
      </div>
      <Source names={pair.evidence} />
    </>
  );
}
