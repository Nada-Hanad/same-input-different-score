import React from "react";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  within,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import source from "../../reproducibility_artifact/data/research.json";
import { App } from "./main";
import type { Research } from "./model";
const data = source as unknown as Research;
beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
  localStorage.clear();
});
function renderAt(view: string) {
  window.history.replaceState(null, "", `/?view=${encodeURIComponent(view)}`);
  return render(<App data={data} />);
}
describe("research platform interactions", () => {
  it("navigates all seven sections", async () => {
    renderAt("Overview");
    const user = userEvent.setup();
    for (const p of [
      "Release Explorer",
      "Remediation Plans",
      "Mechanisms",
      "Population Effects",
      "Release-Impact Audit",
      "Artifact",
    ]) {
      await user.click(within(screen.getByRole("navigation")).getByText(p));
      expect(screen.getByRole("heading", { level: 1, name: p })).toBeTruthy();
    }
  });
  it("selects a zero-change pair and persists its URL", async () => {
    renderAt("Release Explorer");
    fireEvent.change(screen.getByLabelText("Release pair"), {
      target: { value: "1.3.2->1.3.3" },
    });
    expect(screen.getByRole("heading", { name: "1.3.2 → 1.3.3" })).toBeTruthy();
    expect(window.location.hash).toContain("pair=1.3.2-%3E1.3.3");
    expect(screen.getAllByText("No test-outcome differences were observed on the fixed reference corpus.").length).toBeGreaterThan(
      0,
    );
  });
  it("filters failing plans and changes target", async () => {
    renderAt("Remediation Plans");
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "A+ 100+" }));
    expect(
      screen.getByRole("heading", { name: "1.5.2 → 1.5.3 · target A+" }),
    ).toBeTruthy();
    await user.selectOptions(
      screen.getByLabelText("Plan-analysis coverage"),
      "failures",
    );
    expect(window.location.hash).toContain("coverage=failures");
    expect(window.location.hash).toContain("target=A%2B");
  });
  it("searches provenance with a useful empty state", async () => {
    renderAt("Artifact");
    fireEvent.change(screen.getByLabelText("Search result-to-evidence index"), {
      target: { value: "393" },
    });
    expect(
      screen.getByText(/393 score changes; 278 grade changes across/),
    ).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Search result-to-evidence index"), {
      target: { value: "zz-unmatched" },
    });
    expect(screen.getByText(/No evidence entries match/)).toBeTruthy();
  });
  it("keeps missing population intervals unavailable", () => {
    renderAt("Population Effects");
    expect(screen.getAllByText("Not recorded").length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Comparison release"), {
      target: { value: "1.7.1" },
    });
    expect(
      screen.getByText(/Not available for this selected measurement\/pair/),
    ).toBeTruthy();
  });
  it("changes the audit report and preserves validation failures", () => {
    renderAt("Release-Impact Audit");
    fireEvent.change(
      screen.getByLabelText("Precomputed release-impact report"),
      { target: { value: "0" } },
    );
    expect(
      screen.getByText(/An observed zero has a coverage boundary/),
    ).toBeTruthy();
    cleanup();
    renderAt("Artifact");
    expect(screen.getByText(/Failed: 169\/195 exact/)).toBeTruthy();
  });
  it("offers a persistent optional dark theme", async () => {
    renderAt("Overview");
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Switch to dark theme" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
  });
});

describe("second-pass research controls", () => {
  it("shows both exposure conditions without an obsolete CI warning", () => {
    renderAt("Release Explorer");
    fireEvent.change(screen.getByLabelText("Release pair"), {
      target: { value: "1.3.8->1.4.0" },
    });
    expect(screen.getByText("Registered exposure condition")).toBeTruthy();
    expect(
      screen.getByText("Corrected parser-faithful exposure condition"),
    ).toBeTruthy();
    expect(screen.queryByText("Manuscript interval discrepancy.")).toBeNull();
  });
  it("selects sampled-only and full-only plan coverage with a shareable URL", () => {
    renderAt("Remediation Plans");
    fireEvent.change(screen.getByLabelText("Plan-analysis coverage"), {
      target: { value: "sampled" },
    });
    expect(window.location.hash).toContain("coverage=sampled");
    expect(
      screen.getByRole("img", {
        name: "Failing minimum-action B plans by release pair",
      }).textContent,
    ).toContain("sample");
    fireEvent.change(screen.getByLabelText("Plan-analysis coverage"), {
      target: { value: "full" },
    });
    expect(window.location.hash).toContain("coverage=full");
  });
  it("uses selected mechanism pair as the default", () => {
    renderAt("Mechanisms");
    expect(
      (screen.getByLabelText("All supported changes") as HTMLInputElement)
        .checked,
    ).toBe(false);
    fireEvent.change(screen.getByLabelText("Release pair"), {
      target: { value: "1.3.2->1.3.3" },
    });
    expect(
      screen.getByText(
        "No scoring-relevant implementation change was identified for this pair. No test-outcome differences were observed on the fixed reference corpus.",
      ),
    ).toBeTruthy();
  });
  it("changes the executed synthetic tied-plan example", () => {
    renderAt("Remediation Plans");
    fireEvent.change(screen.getByLabelText("Synthetic experiment"), {target:{value:"parser"}});
    fireEvent.change(screen.getByLabelText("Tied minimum-action plan"), {
      target: { value: "1" },
    });
    expect((screen.getByLabelText("Tied minimum-action plan") as HTMLSelectElement).selectedOptions[0].text).toBe("Content-type options");
    expect(screen.getByText(/No newer subset reaches B/)).toBeTruthy();
  });
  it("filters population families/tests and persists shareable sorting", () => {
    renderAt("Population Effects");
    fireEvent.change(screen.getByLabelText("Measurement family"), {
      target: { value: "Test outcomes" },
    });
    fireEvent.change(screen.getByLabelText("Security test group"), {
      target: { value: "Subresource Integrity" },
    });
    fireEvent.change(screen.getByLabelText("Sort measurements"), {
      target: { value: "signed" },
    });
    expect(window.location.hash).toContain("pop_sort=signed");
    fireEvent.click(screen.getByLabelText("Show exact outcome identifiers"));
    expect(window.location.hash).toContain("raw=true");
  });
  it("shows all three evidence access categories and public links", () => {
    renderAt("Artifact");
    fireEvent.change(screen.getByLabelText("Evidence access"), {
      target: { value: "Reproducible using public fixtures" },
    });
    expect(
      screen.getByText(/Real scorer fixed-input differences/),
    ).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: "Included result dataset ↓" })
        .getAttribute("href"),
    ).toBe("./data/synthetic-replay.json");
  });
  it("renders an audit command as a genuine single line without stray backslashes", () => {
    renderAt("Release-Impact Audit");
    const pre = document.querySelector("pre")!;
    expect(pre.textContent).toContain("--candidate-replay replay");
    expect(pre.textContent).not.toContain("\\ --in");
    expect(screen.getByText("Compare precomputed audits")).toBeTruthy();
  });
});

describe("final research walkthrough",()=>{
  it("defaults to the actual unchanged-score demonstration",()=>{
    renderAt("Remediation Plans");
    expect(screen.getByText("Same original score. A failing plan.")).toBeTruthy();
    expect(screen.getByText("-35")).toBeTruthy();
    expect(screen.getByText("-80")).toBeTruthy();
    expect(screen.getByText("25 / D- · fails B")).toBeTruthy();
  });
  it("links a pair directly to its mechanisms and population comparison",()=>{
    renderAt("Release Explorer");
    expect(screen.getByRole("link",{name:"Inspect mechanisms →"}).getAttribute("href")).toContain("1.5.2-%3E1.5.3");
    expect(screen.getByRole("link",{name:"Compare population measurements →"}).getAttribute("href")).toContain("from=1.5.2&to=1.5.3");
  });
  it("keeps mechanism scope in a shareable URL",()=>{
    renderAt("Mechanisms");
    fireEvent.click(screen.getByLabelText("All supported changes"));
    expect(window.location.hash).toContain("mechanisms=all");
  });
});

it("normalizes a malformed shared population pair",()=>{
  window.history.replaceState(null,"","/?view=Population+Effects&pair=invalid");
  render(<App data={data}/>);
  expect((screen.getByLabelText("Baseline release") as HTMLSelectElement).value).toBe("1.5.2");
  expect((screen.getByLabelText("Comparison release") as HTMLSelectElement).value).toBe("1.5.3");
});
