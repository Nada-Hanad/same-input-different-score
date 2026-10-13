import { describe, it, expect } from "vitest";
import source from "../../reproducibility_artifact/data/research.json";
import {
  compareVersions,
  percentage,
  planCounts,
  selectState,
  type Research,
} from "./model";
const data = source as unknown as Research;
describe("research semantics", () => {
  it("uses numeric release order and published releases only", () => {
    expect(compareVersions("1.4.9", "1.4.10")).toBeLessThan(0);
    expect(data.releases).toHaveLength(27);
    expect(data.pairs.map((p) => p.pair)).toEqual(
      data.releases
        .slice(1)
        .map((r, i) => `${data.releases[i].release}->${r.release}`),
    );
  });
  it("distinguishes comparison totals from distinct websites", () => {
    expect(data.pairs.reduce((n, p) => n + p.S, 0)).toBe(393);
    expect(data.summary.unique_failing.B).toBe(125);
    expect(
      data.pairs.reduce(
        (n, p) => n + planCounts(p.plans.B).every + planCounts(p.plans.B).some,
        0,
      ),
    ).toBe(126);
  });
  it("preserves every/some/no failure classification", () => {
    const p = data.pairs.find((p) => p.old === "1.5.2")!.plans.B;
    expect(planCounts(p)).toEqual({ every: 83, some: 0, none: 10245 });
    expect(p.any_invalid_base_unchanged).toBe(18);
  });
  it("uses eligible denominators only for the measured scope", () => {
    const p = data.pairs[0].plans.B;
    expect(planCounts(p).none).toBeNull();
    expect(p.scope).toBe("control-sample");
    expect(p.n).toBe(2205);
  });
  it("does not divide by missing/zero denominators", () => {
    expect(percentage(393, 422864)).toBeCloseTo(0.09294, 4);
    expect(percentage(1, 0)).toBeNull();
  });
  it("validates shareable and invalid selections", () => {
    const s = selectState(
      data,
      "?view=Remediation+Plans&pair=1.5.2-%3E1.5.3&target=A%2B",
    );
    expect(s.target).toBe("A+");
    expect(s.pair.old).toBe("1.5.2");
    expect(selectState(data, "?view=bad&pair=bad&target=bad").page).toBe(
      "Overview",
    );
  });
});

import {
  filterPlanPairs,
  populationRows,
  filterPopulation,
  measurementFamily,
  measurementTest,
} from "./model";
describe("second-pass scientific and filter regressions", () => {
  it("separates full and sampled coverage and failures", () => {
    expect(filterPlanPairs(data.pairs, "B", "all")).toHaveLength(26);
    expect(filterPlanPairs(data.pairs, "B", "full")).toHaveLength(13);
    expect(filterPlanPairs(data.pairs, "B", "sampled")).toHaveLength(13);
    expect(filterPlanPairs(data.pairs, "B", "failures")).toHaveLength(4);
  });
  it("keeps registered/corrected exposure and recorded corrected interval", () => {
    const e = data.pairs.find((p) => p.old === "1.3.8")!.exposure;
    expect(e.registered).toBe(0);
    expect(e.corrected).toBe(41);
    expect(e.corrected_ci95).toEqual([0.0113,0.1488]);
  });
  it("converts fractions to percent and differences to percentage points", () => {
    const r = populationRows(data, "1.5.2", "1.5.3").find(
      (r) =>
        r.id ===
        "outcome sri-not-implemented-and-external-scripts-not-loaded-securely",
    )!;
    expect(r.old).toBeCloseTo(18.39, 2);
    expect(r.next).toBeCloseTo(19.19, 2);
    expect(r.change).toBeCloseTo(0.8, 2);
    expect(r.unit).toContain("percentage points");
  });
  it("preserves absence separately from an observed zero", () => {
    const rows = populationRows(data, "1.3.2", "1.7.1");
    expect(rows.some((r) => r.old === null)).toBe(true);
    expect(rows.some((r) => r.old === 0 || r.next === 0)).toBe(true);
  });
  it("groups outcomes and sorts without imputing missing changes", () => {
    const rows = populationRows(data, "1.5.2", "1.5.3");
    const r = filterPopulation(
      rows,
      "",
      "Test outcomes",
      "Subresource Integrity",
      "absolute",
    );
    expect(r.length).toBeGreaterThan(1);
    expect(r.every((r) => r.test === "Subresource Integrity")).toBe(true);
    expect(Math.abs(r[0].change ?? 0)).toBeGreaterThanOrEqual(
      Math.abs(r[1].change ?? 0),
    );
    expect(measurementFamily("mean score")).toBe("Mean score");
    expect(measurementTest("outcome html-not-parseable")).toBe(
      "Subresource Integrity",
    );
  });
  it("records actual A/A+ set equality without bundled manuscript metadata", () => {
    expect(data.a_aplus_identity.union.same_websites).toBe(true);
    expect(data.a_aplus_identity.union.intersection).toBe(132);
    expect(data).not.toHaveProperty('manuscript');
    expect(data).not.toHaveProperty('paper_available');
  });
});
