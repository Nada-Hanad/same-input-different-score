import {classificationLabel, pairExplanation, implementationReason} from "../classifications";
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
export default function Mechanisms({
  data,
  pair,
  setPair,
}: {
  data: Research;
  pair: Pair;
  setPair: (p: Pair) => void;
}) {
  const [all, setAll] = useState(new URLSearchParams(routeSearch()).get("mechanisms") === "all");
  const entries = data.mechanisms.filter((x) => all || x.pair === pair.pair);
  return (
    <>
      <div className="controls">
        <PairControl data={data} pair={pair} onChange={setPair} />
        <label className="checkbox">
          <input
            type="checkbox"
            checked={all}
            onChange={(e) => {setAll(e.target.checked);const u=routeUrl();u.searchParams.set("mechanisms",e.target.checked?"all":"selected");writeRoute(u);}}
          />
          All supported changes
        </label>
      </div>
      <Callout>
        <strong>Evidence scope.</strong> Source/dependency closure locates
        changed implementation relevant to an outcome. It does not by itself
        isolate every dependency’s causal contribution. Counts are affected test
        assessments and can overlap across tests.
      </Callout>
      <div className="mechanism-grid">
        {entries.map((x, i) => (
          <article className="panel" key={i}>
            <p className="eyebrow">
              {nice(x.pair)} · {classificationLabel(x.class)}
            </p>
            <h3>
              {x.test === "subresource-integrity"
                ? "Subresource Integrity (SRI)"
                : x.test}
            </h3>
            <Stat value={x.sites} label="changed assessments" />
            <p>
              {
                (() => {const entry=data.pairs.find(p=>p.pair===x.pair);return entry ? implementationReason(entry) : "Implementation details not available.";})()
              }
            </p>
            <p>
              <a
                href={`#?view=Release%20Explorer&pair=${encodeURIComponent(x.pair)}`}
              >
                Supporting release entry →
              </a>{" "}
              ·{" "}
              <a
                href={`#?view=Artifact&search=${encodeURIComponent(x.test === "subresource-integrity" ? "parser" : "attribution")}`}
              >
                Evidence index →
              </a>
            </p>
            <details>
              <summary>Inspect implementation provenance</summary>
              <p>Recorded implementation note: {data.pairs.find(p=>p.pair===x.pair)?.release.scoring_change_from_diff || "Not recorded"}</p>
              <ul>
                {x.changed_in_closure.map((f) => (
                  <li key={f}>
                    <code>{f}</code>
                  </li>
                ))}
              </ul>
              <p className="caption">
                Recorded attribution:{" "}
                {x.explained
                  ? "explained within the inspected closure"
                  : "unexplained"}
                . This is the producing analysis’s classification.
              </p>
            </details>
          </article>
        ))}
      </div>
      {!entries.length && (
        <Callout>
          {pair.T === 0 ? pairExplanation(pair) : "No mechanism entry is available for this selection. This does not establish zero outcome changes."}
        </Callout>
      )}
      {(all || pair.old === "1.5.2") && (
        <>
          {" "}
          <section className="feature">
            <p className="eyebrow">PARSER MECHANISM · 1.5.3</p>
            <h2>Resolved URL versus raw attribute</h2>
            <div className="split">
              <article>
                <h3>jsdom</h3>
                <p>
                  Reads the resolved <code>script.src</code> property. A
                  protocol-relative source can resolve through an HTTPS{" "}
                  <code>&lt;base href&gt;</code>.
                </p>
              </article>
              <article>
                <h3>htmlparser2</h3>
                <p>
                  Reads the raw <code>src</code> attribute. The SRI test’s
                  existing rule for a source starting with <code>//</code> is
                  reached instead.
                </p>
              </article>
            </div>
            <p>
              Stored replay outputs place{" "}
              {
                Object.entries(data.parser_mechanism_counts.B).find(([k]) =>
                  k.startsWith(
                    "sri-not-implemented-but-external-scripts-loaded-securely",
                  ),
                )?.[1]
              }{" "}
              of the{" "}
              {
                data.pairs.find((p) => p.old === "1.5.2")!.plans.B.fate
                  .every_fails
              }{" "}
              failing B cases in the secure-to-insecure external-script outcome
              transition. The other failing cases include HTML parseability
              transitions. This explanation is supported by targeted source
              inspection and stored-input diagnostics, not proof that every
              parser change has been isolated.
            </p>
          </section>
          <section className="panel">
            <Table
              rows={data.parser_mechanism_counts.B}
              label="SRI outcome transitions among websites with failing B plans at 1.5.3"
            />
          </section>
        </>
      )}{" "}
      <Callout>
        Exploratory as-deployed dependency analyses use different jsdom
        configurations from the main installed-dependency replay. They are
        described in the evidence manifest and kept separate from the 27-release
        series.
      </Callout>
      <Source
        names={[
          "attribution.json",
          "release_ledger.csv",
          "RESULTS_PLAN_VALIDITY_2026-10-08 §8 and §10",
        ]}
      />
    </>
  );
}
