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
import { pages } from "../model";
export default function Overview({
  data,
  go,
}: {
  data: Research;
  go: (p: (typeof pages)[number]) => void;
}) {
  const s = data.summary;
  return (
    <>
      <div className="hero">
        <p className="eyebrow">THE WEB CONFERENCE 2027 · RESEARCH COMPANION</p>
        <h1>
          Same input.
          <br />
          <em>Different score.</em>
        </h1>
        <p className="lead">
          A software release can change a Web security assessment while the
          website’s responses stay fixed. Explore what changed, why it changed,
          and what the change means for modeled plans.
        </p>
        <button className="primary" onClick={() => go("Release Explorer")}>
          Explore the release pairs <span>↗</span>
        </button>
        <p className="paper-link">
          <button onClick={() => go("Artifact")}>
            Result-to-evidence index →
          </button>
        </p>
        <div className="hero-mark" aria-hidden="true">
          <span>FIXED INPUT</span>
          <div className="mark-line" />
          <div className="mark-releases">
            <i>1.5.2</i>
            <i>1.5.3</i>
          </div>
          <div className="mark-releases">
            <b>{data.pairs.find((p) => p.old === "1.5.2")!.algorithm_old}</b>
            <b>{data.pairs.find((p) => p.old === "1.5.2")!.algorithm_new}</b>
          </div>
          <small>
            Reported algorithm version
            <br />
            unchanged across the parser replacement
          </small>
        </div>
      </div>
      <div className="stats">
        <Stat
          value={s.releases}
          label="published releases"
          detail="1.3.2 through 1.7.1"
        />
        <Stat
          value={s.scored}
          label="scored websites"
          detail={`${fmt(s.collected)} collected websites`}
        />
        <Stat
          value={s.scores}
          label="score changes"
          detail={`${fmt(s.comparisons)} website–release-pair comparisons`}
        />
        <Stat
          value={s.grades}
          label="grade changes"
          detail={`Across ${s.pairs} consecutive release pairs`}
        />
      </div>
      <section className="section-heading">
        <p className="eyebrow">THE MEASUREMENT DESIGN</p>
        <h2>Hold responses fixed. Change the release.</h2>
      </section>
      <div className="method">
        <article>
          <b>01</b>
          <h3>Collect once</h3>
          <p>
            Store website responses from one collection vantage point. Preserve
            the evidence that the tests read.
          </p>
        </article>
        <article>
          <b>02</b>
          <h3>Replay {s.releases} releases</h3>
          <p>
            Run each release’s test and scoring code on the same stored
            evidence. Measure within-input differences.
          </p>
        </article>
        <article>
          <b>03</b>
          <h3>Audit consequences</h3>
          <p>
            Compare test outcomes, scores, grades, population estimates, and
            tied minimum-action plans.
          </p>
        </article>
      </div>
      <div className="split">
        <article className="panel">
          <p className="eyebrow">SCORE STABILITY ≠ PLAN STABILITY</p>
          <h2>{s.unique_failing.B} websites</h2>
          <p>
            Have a failing minimum-action B plan across the 13 full-corpus
            release pairs. The A target count is {s.unique_failing.A}. These are
            distinct websites, not sums of pair counts.
          </p>
          <button onClick={() => go("Remediation Plans")}>
            Inspect plan validity →
          </button>
        </article>
        <article className="panel">
          <p className="eyebrow">REPORTED ALGORITHM VERSION</p>
          <h2>
            {s.unchanged_algorithm_scores} / {s.scores}
          </h2>
          <p>
            Score changes occur while the reported algorithm version stays
            unchanged; {s.unchanged_algorithm_grades} of {s.grades} grade
            changes do too. {s.unchanged_algorithm_failing.B} of{" "}
            {s.unique_failing.B} websites with a failing B plan are affected by
            such pairs.
          </p>
          <button onClick={() => go("Mechanisms")}>
            Trace implementation evidence →
          </button>
        </article>
      </div>
      <Callout tone="warning">
        <strong>Validation boundary.</strong> Live-service exact score agreement
        was {data.gates.live.exact_score}/{data.gates.live.both_scored} (
        {liveRate(data)}%), below the prespecified 90% threshold. Results
        describe fixed-input release contrasts on the collected evidence;
        absolute scores do not establish agreement with Mozilla’s deployed
        service.
      </Callout>
      <Source
        names={[
          "results.json",
          "plan_validity.json",
          "gates.json",
          "release_ledger.csv",
        ]}
      />
    </>
  );
}
