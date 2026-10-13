import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "../hosting";
import React, { useState, useEffect } from "react";
import {
  planCounts,
  filterPlanPairs,
  type Coverage,
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
import PlanDetails from "./PlanDetails";
import WorkedExample from "./WorkedExample";
export default function Plans({
  data,
  pair,
  target,
  setPair,
  setTarget,
}: {
  data: Research;
  pair: Pair;
  target: Target;
  setPair: (p: Pair) => void;
  setTarget: (t: Target) => void;
}) {
  const initialCoverage = new URLSearchParams(routeSearch()).get(
    "coverage",
  );
  const [coverage, setCoverage] = useState<Coverage>(
    ["all", "full", "sampled", "failures"].includes(initialCoverage ?? "")
      ? (initialCoverage as Coverage)
      : "all",
  );
  useEffect(() => {
    const u = routeUrl();
    u.searchParams.set("coverage", coverage);
    writeRoute(u);
  }, [coverage]);
  const plan = pair.plans[target];
  const rows = filterPlanPairs(data.pairs, target, coverage);
  const key = target === "B" ? "T70" : target === "A" ? "T90" : "T100";
  const margins = data.margins["1.7.1"][key];
  return (
    <>
      <div className="controls">
        <PairControl data={data} pair={pair} onChange={setPair} />
        <TargetControl target={target} onChange={setTarget} />
      </div>
      <Callout>
        <strong>Modeled action space.</strong> Nine header actions, 512 subsets.
        A minimum-action plan minimizes action count among subsets reaching the
        target grade under the old release. Every tied minimum-action plan is
        retained. These experiments do not establish safe deployment or actual
        remediation effectiveness.
      </Callout>
      <section className="panel">
        <div className="panel-top">
          <h3>Plan validity across consecutive release pairs</h3>
          <label className="control">
            Plan-analysis coverage
            <select
              value={coverage}
              onChange={(e) => setCoverage(e.target.value as Coverage)}
            >
              <option value="all">All 26 consecutive pairs</option>
              <option value="full">13 full-corpus plan pairs</option>
              <option value="sampled">13 sampled control pairs</option>
              <option value="failures">
                Pairs with observed plan failures
              </option>
            </select>
          </label>
        </div>
        <div className="legend">
          <span>
            <i style={{ background: "var(--accent)" }} />
            Every tied plan fails
          </span>
          <span>
            <i style={{ background: "var(--soft-accent)" }} />
            Some tied plans fail
          </span>
        </div>
        <Bars
          label={`Failing minimum-action ${target} plans by release pair`}
          rows={rows.map((p) => {
            const c = planCounts(p.plans[target]);
            return {
              label:
                nice(p.pair) +
                (p.plans[target].scope === "control-sample"
                  ? " · sample"
                  : " · full"),
              values: [c.every, c.some],
            };
          })}
          colors={["var(--accent)", "var(--soft-accent)"]}
        />
        <p className="caption">
          Website counts within each pair. Rows marked sample use 2,205 control
          websites; remaining pairs use 16,264. Zero bars show no observed plan
          failure within their scope. Distinct failing websites across the 13
          full-corpus pairs: {data.summary.unique_failing[target]}.
        </p>
        <details>
          <summary>Accessible data table and pair navigation</summary>
          <table>
            <thead>
              <tr>
                <th>Release pair</th>
                <th>Every fails</th>
                <th>Some fail</th>
                <th>No failure</th>
                <th>Scope</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => {
                const c = planCounts(p.plans[target]);
                return (
                  <tr
                    key={p.pair}
                    className={
                      p.plans[target].scope === "control-sample"
                        ? "sampled-row"
                        : ""
                    }
                  >
                    <th>
                      <button onClick={() => setPair(p)}>{nice(p.pair)}</button>
                    </th>
                    <td>{c.every}</td>
                    <td>{c.some}</td>
                    <td>
                      {c.none === null
                        ? "Eligible count not recorded"
                        : fmt(c.none)}
                    </td>
                    <td>
                      <span className="badge">
                        {p.plans[target].scope === "control-sample"
                          ? "Sample · 2,205"
                          : "Full corpus · 16,264"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </details>
      </section>
      <div className="pair-title">
        <h2>
          {nice(pair.pair)} · target {target}
        </h2>
        <span className="badge">{plan.scope}</span>
      </div>
      <PlanDetails plan={plan} />
      <details className="panel">
        <summary>
          The nine modeled actions and the exact input fields they modify
        </summary>
        <p className="caption">
          Definitions match the active 512-subset remediate.mjs implementation.
          Its eight header values match actions.mjs; the older prototype used a
          fixed Set-Cookie header, while the study transforms flags on existing
          session-jar cookies. These actions optimize score-target sufficiency
          and may be unsafe or inappropriate in a deployment.
        </p>
        <table>
          <thead>
            <tr>
              <th>Action</th>
              <th>Modeled value</th>
              <th>Stored input changed</th>
            </tr>
          </thead>
          <tbody>
            {data.actions.map((a) => (
              <tr key={a.id}>
                <th>
                  {a.label} <code>{a.id}</code>
                </th>
                <td>
                  <code>
                    {a.value ?? "secure=true; httpOnly=true; sameSite=strict"}
                  </code>
                </td>
                <td>{a.modifies}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      {plan.weighted_any_invalid_all_sites && (
        <section className="panel">
          <h3>Weighted share with any tied plan failure</h3>
          <p>
            Among all scored Tranco websites:{" "}
            <IntervalText value={plan.weighted_any_invalid_all_sites} />
          </p>
          <p>
            Among eligible Tranco websites:{" "}
            <IntervalText value={plan.weighted_any_invalid_eligible} />
          </p>
        </section>
      )}
      <WorkedExample data={data} />
      <section className="feature">
        <p className="eyebrow">THE 1.5.2 → 1.5.3 PARSER REPLACEMENT</p>
        <h2>A stable score can hide a failed plan.</h2>
        <p>
          Every B-target minimum-action plan fails for{" "}
          {data.pairs.find((p) => p.old === "1.5.2")!.plans.B.fate.every_fails}{" "}
          websites.{" "}
          {
            data.pairs.find((p) => p.old === "1.5.2")!.plans.B
              .any_invalid_base_unchanged
          }{" "}
          have unchanged original scores. Under the nine-action model,{" "}
          {
            data.pairs.find((p) => p.old === "1.5.2")!.plans.B
              .additional_effort_min?.["99"]
          }{" "}
          B targets have no modeled extension restoring the target;{" "}
          {
            data.pairs.find((p) => p.old === "1.5.2")!.plans.B
              .additional_effort_min?.["1"]
          }{" "}
          can be restored with one additional action.
        </p>
        <p>
          The SRI test changes the treatment of protocol-relative script sources
          when jsdom’s resolved URLs are replaced with raw attributes from
          htmlparser2. The response body stays fixed; header actions cannot
          alter the script body.
        </p>
        <p className="caption">
          Empirical response fixtures remain restricted. The worked example
          above uses public synthetic responses and actual scorer execution.
        </p>
      </section>
      <section className="panel">
        <h3>The 90-point uncurved-score threshold</h3>
        <p>
          The uncurved score starts at 100 and includes nonpositive score
          modifiers. Positive score modifiers count only when it reaches 90. The
          final score is floored at zero: two different negative uncurved scores
          can both display zero. Displayed score margins can therefore hide a
          plan’s proximity to failure.
        </p>
        <Bars
          label={`Uncurved and displayed minimum-plan margins under 1.7.1, target ${target}`}
          rows={[
            {
              label: "Uncurved margin = 0",
              values: [margins.uncurved_margin["0"] ?? 0],
            },
            {
              label: "Displayed margin = 0",
              values: [margins.displayed_margin["0"] ?? 0],
            },
            {
              label: "All minimum-action plans",
              values: [margins.optimal_plans],
            },
          ]}
        />
        <p className="caption">
          Counts of plans, not websites. Stored margin analysis for release
          1.7.1 and target {target}; no prediction of future release robustness.
        </p>
      </section>
      <Callout>
        A and A+ failure identities were compared independently: the same
        affected website sets occur in every one of the 13 full-corpus pairs,
        and both unions contain {data.a_aplus_identity.union.A} websites. This
        observed equality does not establish a general equivalence of targets or
        plan families.
      </Callout>
      <Source
        names={[
          "plan_validity.json",
          "plan_validity_units/*.jsonl.gz",
          "plan_validity.py",
        ]}
      />
    </>
  );
}
