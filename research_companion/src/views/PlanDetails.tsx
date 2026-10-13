import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "../hosting";
import React, { useState, useEffect } from "react";
import {
  planCounts,
  percentage,
  download,
  type Research,
  type Pair,
  type Target,
  type Plan,
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
export default function PlanDetails({ plan }: { plan: Plan }) {
  const c = planCounts(plan);
  const noFailures = plan.fate.every_fails === 0 && plan.fate.some_fail === 0;
  const noChangedFamilies = plan.category != null && plan.eligible != null
    && Object.values(plan.category).reduce((total,n)=>total+n,0) === plan.eligible
    && Object.entries(plan.category).filter(([k])=>k!=="identical").every(([,n])=>n===0);
  return (
    <>
      <div className="stats">
        <Stat value={c.every} label="every tied plan fails" />
        <Stat value={c.some} label="some tied plans fail" />
        <Stat
          value={plan.any_invalid_base_unchanged ?? "Not recorded"}
          label="failing with original score unchanged"
        />
        <Stat
          value={plan.eligible === null ? "Not recorded" : plan.eligible}
          label="previously sufficient plan exists"
          detail="Website originally below target"
        />
      </div>
      <section className="panel">
        <h3>Can a modeled action subset restore the target?</h3>
        {plan.restoration ? (
          <p>
            Among {fmt(plan.restoration.failing_websites)} affected websites,{" "}
            {fmt(plan.restoration.any_subset_restores)} have some sufficient
            newer-release subset and {fmt(plan.restoration.no_subset_reaches)}{" "}
            have none in the nine-action space. These are website counts within
            this release pair.
          </p>
        ) : (
          <p>
            Not evaluated for the full corpus. Target-specific restoration
            counts are not recorded for the control sample.
          </p>
        )}
      </section>
      {plan.note && <Callout>{plan.note}</Callout>}
      <details className="panel"><summary>Inspect minimum-plan classifications and restoration effort</summary>
      {plan.category && (
        <div className="split">
          <section className="panel">
            <Table
              label="New minimum-plan family classification"
              rows={Object.fromEntries(
                Object.entries(plan.category).map(([k, v]) => [
                  (
                    {
                      identical: "Minimum-plan family unchanged",
                      cheaper: "Fewer minimum actions",
                      costlier: "More minimum actions",
                      expanded: "Additional tied minimum plans",
                      out_of_reach: "No subset reaches target",
                      met_without_action: "Target met without an action",
                      hidden_invalidation:
                        "Tied family changes at same action count",
                    } as Record<string, string>
                  )[k] ?? k,
                  v,
                ]),
              )}
            />
          </section>
          <section className="panel">
            <Table
              label="Additional actions to extend a failing plan (best extension)"
              emptyLabel={plan.additional_effort_min != null && noFailures ? "No failing plans were observed under this pair’s recorded coverage." : "Not recorded"}
              rows={Object.fromEntries(
                Object.entries(plan.additional_effort_min ?? {}).map(
                  ([k, v]) => [
                    k === "99"
                      ? "No modeled extension reaches target"
                      : `${k} additional action${k === "1" ? "" : "s"}`,
                    v,
                  ],
                ),
              )}
            />
            <p className="caption">
              Counts among websites with a failing plan. Extending an old plan
              differs from searching for any sufficient new subset.
            </p>
          </section>
        </div>
      )}
      {plan.action_count_transitions && (
        <section className="panel">
          <Table
            rows={plan.action_count_transitions}
            label="Minimum action counts among changed plan families only"
            emptyLabel={noChangedFamilies ? "No changed minimum-plan families were observed under the recorded coverage." : "Not recorded"}
          />
          <p className="caption">
            Counts derived from stored changed-unit records; unchanged plan
            families are omitted.
          </p>
        </section>
      )}
      </details>
    </>
  );
}
