import {manuscriptLocation, figureDescription} from "../references";
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
export default function Artifact({ data }: { data: Research }) {
  const [search, setSearch] = useState(
    new URLSearchParams(routeSearch()).get("search") ?? "",
  );
  const [access, setAccess] = useState("All");
  const [rq, setRQ] = useState("All");
  const matches = data.manifest.filter(
    (x) =>
      (rq === "All" || x.rq.includes(rq)) &&
      (access === "All" || x.access_category === access) &&
      `${x.claim} ${x.source} ${x.id}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <>
      <div className="split">
        <section className="panel">
          <p className="eyebrow">PUBLIC AGGREGATES · RESTRICTED RESPONSES</p>
          <h2>Follow a result to its evidence.</h2>
          <p>
            The public artifact rebuilds and validates aggregate views. Full
            scorer replay and empirical regeneration require the retained
            website-response corpus and pinned release environments.
          </p>
          <div className="buttons">
            <a className="button" href={resource("downloads/scientific-artifact.zip")} download>Download verified scientific archive ↓</a>
            <a className="button" href={resource("data/release-pair-baseline.csv")} download>Download original release comparison CSV ↓</a>
            <a className="button primary" href={resource("/data/research.json")}  download>
              Download aggregate dataset ↓
            </a>
            <a className="button" href={resource("/docs/REPRODUCIBILITY.md")}  download>
              Reproducibility guide ↓
            </a>
            <a
              className="button"
              href={resource("/docs/METHODS_AND_LIMITATIONS.md")}
              download
            >
              Limitations ↓
            </a>
          </div>
        </section>
        <section className="panel">
          <h3>Validation results stay visible</h3>
          <dl>
            <dt>V1 · storage fidelity</dt>
            <dd>
              {data.gates.storage.exact}/{data.gates.storage.of} exact
            </dd>
            <dt>V2 · live-service agreement</dt>
            <dd className="failure">
              Failed: {data.gates.live.exact_score}/
              {data.gates.live.both_scored} exact, {liveRate(data)}% &lt; 90%
            </dd>
            <dt>V3 · compatibility</dt>
            <dd>
              Fails as originally worded; all inputs scored at collection pass.
            </dd>
            <dt>Memo rerun completeness</dt>
            <dd>
              1.5.0: {data.gates.memo["1.5.0"].rerun_ok}/
              {data.gates.memo["1.5.0"].sampled} completed,{" "}
              {data.gates.memo["1.5.0"].process_failures} process failures.
              Completed vectors match.
            </dd>
          </dl>
        </section>
      </div>
      <div className="controls">
        <label className="control wide">
          Search result-to-evidence index
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Try parser, 393, validation, population…"
          />
        </label>
        <label className="control">
          Research question
          <select value={rq} onChange={(e) => setRQ(e.target.value)}>
            {["All", "RQ1", "RQ2", "RQ3"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
      </div>
      <label className="control wide">
        Evidence access
        <select value={access} onChange={(e) => setAccess(e.target.value)}>
          {[
            "All",
            "Included and downloadable",
            "Reproducible using public fixtures",
            "Restricted original data required",
          ].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </label>
      <section className="panel">
        <h3>Evidence and reproducibility</h3>
        <p><a href={resource("/docs/REPRODUCIBILITY.md")} download>Reproduce public experiments ↓</a> · <a href={resource("/docs/METHODS_AND_LIMITATIONS.md")} download>Methods and limitations ↓</a> · <a href={resource("/docs/EVIDENCE_MAP.md")} download>Evidence map ↓</a> · <a href={resource("/docs/FIGURES.md")} download>Figures and regeneration ↓</a></p>
        <p className="caption">Trace reported results to included datasets, producing code and access requirements. Public aggregate verification and synthetic scorer replay are distinct from complete empirical replay with restricted inputs.</p>
        <p><a href={resource("/data/figure-references.json")} download>Figure correspondence ↓</a> · <a href={resource("/data/download-manifest.json")} download>Download hashes ↓</a></p>
        <a href={resource("/data/scientific-verification.json")}  download>
          Download A/A+ verification metadata ↓
        </a>
      </section>
      <p className="caption">
        {matches.length} evidence entries. Script and source paths below are
        identifiers in the local research workspace, not public download links.
      </p>
      <div className="evidence-list">
        {matches.map((x) => (
          <article className="panel" key={x.id}>
            <div className="panel-top">
              <span className="badge">{x.rq}</span>
              <small>{manuscriptLocation(x)}</small>
            </div>
            <h3>{x.claim}</h3>
            <p>
              <span className="badge">{x.access_category}</span> <span className="badge">{x.result_kind}</span>
            </p>
            <p>
              <a href={resource(x.included_dataset_url)} download>
                Included result dataset ↓
              </a>
              {x.access_category === "Reproducible using public fixtures" && (
                <>
                  {" "}
                  ·{" "}
                  <a href={resource("/docs/REPRODUCIBILITY.md")}  download>
                    Public fixture instructions ↓
                  </a>
                </>
              )}
            </p>
            <dl>
              <dt>Dataset</dt>
              <dd>
                <code>{x.source}</code>
              </dd>
              <dt>Analysis script</dt>
              <dd>
                <code>{x.script}</code>
                {x.script_download_url && (
                  <p>
                    <a href={resource(x.script_download_url)} download>
                      Included producing script ↓
                    </a>
                  </p>
                )}
              </dd>
              {x.figure && (
                <>
                  <dt>Figure</dt>
                  <dd>
                    <p>{figureDescription(x.figure)}</p><code>{x.figure}</code>{x.figure_download_url && <p><a href={resource(x.figure_download_url)} download>Regenerated public figure ↓</a></p>}
                  </dd>
                </>
              )}
              <dt>Configuration</dt>
              <dd>{x.configuration}</dd>
            </dl>
            <details>
              <summary>
                Reproduction command, hashes, and access requirements
              </summary>
              <p className="caption">
                Commands for bundled tools run from reproducibility_artifact.
                Original-study command paths identify the retained research
                workspace; use the included reproducibility guide for the copied
                source layout.
              </p>
              <pre>{x.command}</pre>
              <p>
                {x.verification_method ?? x.evidence_level}. {x.qualification}{" "}
                {x.restricted_inputs
                  ? "Full empirical regeneration requires restricted original inputs."
                  : "This command uses included data or public fixtures; optional scorer installation is documented separately."}
              </p>
              <p className="hash">
                Original source SHA-256:{" "}
                {x.source_sha256 ??
                  "See download-manifest.json for this generated dataset"}
                <br />
                Script SHA-256: {x.script_sha256}
              </p>
            </details>
          </article>
        ))}
      </div>
      {matches.length === 0 && (
        <Callout>
          No evidence entries match this filter. Try another term or select all
          research questions.
        </Callout>
      )}
      <section className="panel">
        <h3>Missing evidence and review boundaries</h3>
        <ul>
          {data.missing.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
        <p>
          The original analysis plan is locally hashed; later 512-subset,
          plan-age, and audit analyses are subsequently prespecified.
          As-deployed dependency checks and the D20 disclosure, population,
          parsing-diagnostic and alternative-CSP follow-ups remain exploratory.
          Original preregistration and deviation files are retained locally
          because they include identifiers and workspace metadata.
        </p>
      </section>
    </>
  );
}
