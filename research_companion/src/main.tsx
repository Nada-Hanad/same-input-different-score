import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "./hosting";
import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import { pages, selectState, type Research, type Target } from "./model";
import "./style.css";
import Overview from "./views/Overview";
import Releases from "./views/Releases";
import Plans from "./views/Plans";
import Mechanisms from "./views/Mechanisms";
import Population from "./views/Population";
import Audits from "./views/Audits";
import Artifact from "./views/Artifact";
const descriptions: Record<(typeof pages)[number], [string, string]> = {
  Overview: ["", ""],
  "Release Explorer": [
    "RQ1 / RQ2",
    "Follow a release from implementation change to assessment outcome.",
  ],
  "Remediation Plans": [
    "RQ3",
    "Test every tied minimum-action plan under the next release.",
  ],
  Mechanisms: [
    "RQ2",
    "Trace outcome variation to scoring rules, parsers, and dependencies.",
  ],
  "Population Effects": [
    "RQ1",
    "Compare population measurements on the same stored responses.",
  ],
  "Release-Impact Audit": [
    "RQ3",
    "Inspect precomputed candidate and positive-control reports.",
  ],
  Artifact: [
    "REPRODUCIBILITY",
    "Find the source, script, configuration, and access boundary behind a result.",
  ],
};
function ExportPreview({value,close}:{value:{name:string;text:string};close:()=>void}) {
  const text=useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{const previous=document.activeElement as HTMLElement|null;text.current?.focus();return ()=>previous?.focus();},[]);
  return <div className="export-dialog" role="dialog" aria-modal="true" aria-label="Filtered public data" onKeyDown={e=>{
    if(e.key==='Escape'){e.preventDefault();close();}
    if(e.key==='Tab'){
      const controls=e.currentTarget.querySelectorAll<HTMLElement>('textarea,button');
      if(e.shiftKey && document.activeElement===controls[0]){e.preventDefault();controls[controls.length-1]?.focus();}
      else if(!e.shiftKey && document.activeElement===controls[controls.length-1]){e.preventDefault();controls[0]?.focus();}
    }
  }}><h2>{value.name}</h2><p>This hosting sandbox blocks downloads. Select and copy the JSON below, or download the complete artifact through the anonymous repository view.</p><textarea ref={text} aria-label="Filtered JSON to copy" readOnly value={value.text}/><button onClick={close}>Close data preview</button></div>;
}
export function App({ data: initialData }: { data: Research }) {
  const [data, setData] = useState(initialData);
  const [exported,setExported]=useState<{name:string;text:string}|null>(null);
  useEffect(()=>{const f=(e:Event)=>setExported((e as CustomEvent).detail);window.addEventListener("artifact-export",f);return ()=>window.removeEventListener("artifact-export",f);},[]);
  const [populationError, setPopulationError] = useState("");
  const initial = selectState(data, routeSearch());
  const [page, setPage] = useState(initial.page);
  const [pair, setPair] = useState(initial.pair);
  const [target, setTarget] = useState<Target>(initial.target);
  useEffect(() => {
    if(page !== "Population Effects" || Object.keys(data.population.levels).length) return;
    let active = true;
    loadData("population")
      .then(extra=>{if(active) setData(d=>({...d,...extra}));})
      .catch(e=>{if(active) setPopulationError(String(e));});
    return ()=>{active=false;};
  },[page,data.population.levels]);
  const [dark, setDark] = useState(
    () => storedTheme(),
  );
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    storeTheme(dark);
  }, [dark]);
  useEffect(() => {
    const u = routeUrl();
    u.searchParams.set("view", page);
    u.searchParams.set("pair", pair.pair);
    u.searchParams.set("target", target);
    writeRoute(u);
    document.title = `${page} · Same Input, Different Score`;
  }, [page, pair, target]);
  useEffect(() => {
    const f = () => {
      const s = selectState(data, routeSearch());
      setPage(s.page);
      setPair(s.pair);
      setTarget(s.target);
    };
    window.addEventListener("popstate", f);
    window.addEventListener("hashchange",f);
    window.addEventListener("artifact-route",f);
    return () => {window.removeEventListener("popstate", f);window.removeEventListener("hashchange",f);window.removeEventListener("artifact-route",f);};
  }, [data]);
  const go = (p: (typeof pages)[number]) => {
    const u = routeUrl();
    u.searchParams.set("view", p);
    if(p==="Population Effects"){u.searchParams.set("from",pair.old);u.searchParams.set("to",pair.new);}
    writeRoute(u,false);
    setPage(p);
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  return (
    <>
      <a className="skip" href="#main" onClick={e=>{e.preventDefault();document.getElementById("main")?.focus();document.getElementById("main")?.scrollIntoView();}}>
        Skip to content
      </a>
      {exported && <ExportPreview value={exported} close={()=>setExported(null)}/> }
      <header>
        <a
          href="#?view=Overview"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            go("Overview");
          }}
        >
          <span className="brand-icon">≠</span>
          <span>
            Same Input,
            <br />
            <b>Different Score</b>
          </span>
        </a>
        <span className="header-note">
          FIXED-INPUT REPLAY
          <br />
          <b>MDN HTTP OBSERVATORY</b>
        </span>
        <button
          className="theme"
          aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
          onClick={() => setDark(!dark)}
        >
          {dark ? "☀ Light" : "◐ Dark"}
        </button>
      </header>
      <div className="shell">
        <nav aria-label="Research sections">
          {pages.map((p, i) => (
            <a
              key={p}
              aria-current={page === p ? "page" : undefined}
              href={`#?view=${encodeURIComponent(p)}&pair=${encodeURIComponent(pair.pair)}&target=${encodeURIComponent(target)}`}
              onClick={(e) => {
                e.preventDefault();
                go(p);
              }}
            >
              <small>0{i + 1}</small>
              {p}
            </a>
          ))}
          <div className="nav-note">
            <b>{data.summary.releases} releases. One fixed corpus.</b>
            <p>
              Aggregate evidence only.
              <br />
              No live scans or tracking.
            </p>
          </div>
        </nav>
        <main id="main" tabIndex={-1}>
          {page !== "Overview" && (
            <section className="page-heading">
              <p className="eyebrow">{descriptions[page][0]}</p>
              <h1>{page}</h1>
              <p className="lead">{descriptions[page][1]}</p>
            </section>
          )}
          {page === "Overview" ? (
            <Overview data={data} go={go} />
          ) : page === "Release Explorer" ? (
            <Releases data={data} pair={pair} setPair={setPair} />
          ) : page === "Remediation Plans" ? (
            <Plans
              data={data}
              pair={pair}
              target={target}
              setPair={setPair}
              setTarget={setTarget}
            />
          ) : page === "Mechanisms" ? (
            <Mechanisms data={data} pair={pair} setPair={setPair} />
          ) : page === "Population Effects" ? (
            Object.keys(data.population.levels).length ? <Population data={data} /> : <p role="status">{populationError || "Loading population measurements…"}</p>
          ) : page === "Release-Impact Audit" ? (
            <Audits data={data} />
          ) : (
            <Artifact data={data} />
          )}
          <footer>
            <span>
              Same Input, Different Score · Anonymous research companion
            </span>
            <span>Fixed inputs · Evidence-linked results · Local preview</span>
          </footer>
        </main>
      </div>
    </>
  );
}
function Loader() {
  const [data, setData] = useState<Research | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    loadData("core")
      .then((d) => {
        if (d.schema_version !== 1 || d.pairs?.length !== 26)
          throw Error("Unsupported or incomplete dataset");
        setData(d);
      })
      .catch((e) => setError(String(e)));
  }, []);
  return data ? (
    <App data={data} />
  ) : (
    <div className="load">
      <h1>
        {error ? "Research data unavailable" : "Loading verified results…"}
      </h1>
      {error && (
        <>
          <p>{error}</p>
          <p>Run the documented data-preparation command, then reload.</p>
          <button onClick={() => window.location.reload()}>
            Reload dataset
          </button>
        </>
      )}
    </div>
  );
}
const rootElement = document.getElementById("root");
if (rootElement) createRoot(rootElement).render(<Loader />);
