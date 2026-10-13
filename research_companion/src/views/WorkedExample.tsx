import {routeSearch,routeUrl,writeRoute,resource,storedTheme,storeTheme,loadData} from "../hosting";
import React, { useState, useEffect } from "react";
import { testNames, type Research } from "../model";
import { Callout } from "../components";
export default function WorkedExample({ data }: { data: Research }) {
  const q=new URLSearchParams(routeSearch());
  const [fixture, setFixture] = useState(q.get('fixture')==='parser'?'parser':'flooring');
  const [index, setIndex] = useState(q.get('example_plan')==='1'?1:0);
  const [stage, setStage] = useState(q.get('example_stage')==='plan'?'plan':'original');
  useEffect(()=>{const u=routeUrl();u.searchParams.set('fixture',fixture);u.searchParams.set('example_plan',String(index));u.searchParams.set('example_stage',stage);writeRoute(u);},[fixture,index,stage]);
  const floor = fixture === 'flooring';
  const original = floor ? data.synthetic_flooring.original : data.synthetic_replay.parser;
  const plan = floor ? data.synthetic_flooring.plan : data.synthetic_replay.plan;
  const p = plan.tied_minimum_plans[Math.min(index, plan.tied_minimum_plans.length-1)];
  const results = stage === 'original' ? original : p;
  return <section className="feature">
    <p className="eyebrow">PUBLIC SYNTHETIC INPUT · GENUINE SCORER EXECUTION</p>
    <h2>{floor ? 'Same original score. A failing plan.' : 'Follow a minimum-action plan across the parser release.'}</h2>
    <p>{floor ? 'Both releases display zero for the same deliberately constructed response. Different negative uncurved scores are concealed by flooring. After the same modeled actions remove other penalties, the older release reaches B and the newer release does not.' : 'The fixed synthetic response contains an HTTPS base and a protocol-relative external script. Historical scorer code produces a different SRI outcome.'} These examples are separate from empirical website counts.</p>
    <div className="controls">
      <label className="control">Synthetic experiment<select value={fixture} onChange={e=>{setFixture(e.target.value);setIndex(0);setStage('original');}}><option value="flooring">Unchanged original score: flooring conceals plan failure</option><option value="parser">Changed original score: parser transition</option></select></label>
      <label className="control">Tied minimum-action plan<select value={Math.min(index,plan.tied_minimum_plans.length-1)} onChange={e=>setIndex(Number(e.target.value))}>{plan.tied_minimum_plans.map((x,i)=><option key={i} value={i}>{x.actions.map(a=>data.actions.find(x=>x.id===a)?.label??a).join(' + ')}</option>)}</select></label>
    </div>
    <p className="caption">Fixed stored input → original assessment → {plan.minimum_actions} modeled actions → new release → plan failure. All 512 subsets were executed per release; {plan.tied_minimum_plans.length} minimum-action plan{plan.tied_minimum_plans.length===1?'':'s'} checked.</p>
    <div className="table-scroll"><table><caption>Actual scorer results · target B (70)</caption><thead><tr><th>Stage</th><th>1.5.2 displayed / grade</th><th>1.5.2 uncurved</th><th>1.5.3 displayed / grade</th><th>1.5.3 uncurved</th></tr></thead><tbody>
      <tr><th>Original synthetic input</th><td>{original.old.score} / {original.old.grade}</td><td>{original.old.uncurved}</td><td>{original.new.score} / {original.new.grade}</td><td>{original.new.uncurved}</td></tr>
      <tr><th>Same minimum-action plan</th><td>{p.old.score} / {p.old.grade} · reaches B</td><td>{p.old.uncurved}</td><td>{p.new.score} / {p.new.grade} · fails B</td><td>{p.new.uncurved}</td></tr>
    </tbody></table></div>
    <Callout>Every tied old minimum-action plan fails in this fixture. No newer subset reaches B; maximum newer score {plan.maximum_new_score}. The SRI modifier changes from −5 to −50. The newer parser reads the raw protocol-relative script attribute, whereas the older parser resolves it through the HTTPS base.</Callout>
    <details><summary>Inspect the actual modeled modifications</summary>{p.actions.map(a=>{const action=data.actions.find(x=>x.id===a)!;return <div key={a}><h3>{action.label}</h3><p>{action.modifies}</p>{action.value&&<pre>{action.header}: {action.value}</pre>}</div>;})}<p>The CSP action also supplies frame-ancestors, affecting the frame-options test. Cookie flags modify only the explicitly synthetic cookie. Actions do not alter the script, redirect chain or reference lists.</p></details>
    <details><summary>Inspect actual test outcomes and score modifiers</summary><label className="control">Assessment stage<select value={stage} onChange={e=>setStage(e.target.value)}><option value="original">Original fixed input</option><option value="plan">After the same modeled plan</option></select></label><div className="table-scroll"><table><thead><tr><th>Test</th><th>1.5.2 outcome / modifier</th><th>1.5.3 outcome / modifier</th></tr></thead><tbody>{Object.keys(results.old.tests).map(k=><tr key={k}><th>{testNames[k]??k}</th><td><code>{results.old.tests[k]}</code> / {results.old.mods[k]}</td><td><code>{results.new.tests[k]}</code> / {results.new.mods[k]}</td></tr>)}</tbody></table></div></details>
    <div className="buttons"><a href={resource(floor?'/data/synthetic-flooring.json':'/data/synthetic-replay.json')} download>Download executed fixture outputs ↓</a><a href={resource("/examples/flooring-input.json")}  download>Inspect synthetic stored input ↓</a><a href={resource("/examples/run.mjs")}  download>Inspect runnable harness source ↓</a><a href={resource("/docs/REPRODUCIBILITY.md")}  download>Run this fixture locally ↓</a></div>
  </section>;
}
