import React from 'react';
import {afterEach, beforeEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen, within} from '@testing-library/react';
import source from '../../reproducibility_artifact/data/research.json';
import catalogue from '../../docs/figure-references.json';
import {App} from './main';
import PlanDetails from './views/PlanDetails';
import {fmt, IntervalText, Table} from './components';
import {percentage, type Pair, type Research} from './model';
import {classificationLabel, classificationMeaning, pairExplanation} from './classifications';
import {manuscriptLocation, figureDescription} from './references';
const data=source as unknown as Research;
beforeEach(()=>{window.scrollTo=vi.fn();history.replaceState(null,'','/REPOSITORY/');});
afterEach(()=>{cleanup();history.replaceState(null,'','/');});
function at(view:string,pair='1.3.2->1.3.3',current=data){
 history.replaceState(null,'',`/REPOSITORY/#?view=${encodeURIComponent(view)}&pair=${encodeURIComponent(pair)}&target=B`);
 return render(<App data={current}/>);
}
it('describes all four recorded classes and distinguishes the code string from missing data',()=>{
 expect(classificationLabel('null')).toBe('No scoring-relevant change');
 expect(classificationLabel('refactor')).toBe('Behavior-preserving refactor');
 expect(classificationLabel('defensive')).toBe('Input handling change');
 expect(classificationLabel('scoring')).toBe('Scoring-relevant change');
 expect(classificationLabel(null)).toBe('Not recorded');expect(classificationLabel(undefined)).toBe('Not recorded');expect(classificationLabel('unknown')).toBe('Not available');
 expect(classificationMeaning('refactor')).toContain('expected');
});
it('never infers implementation class from an observed zero',()=>{
 const zeroGuard=data.pairs.find(p=>p.pair==='1.3.3->1.3.5')!;
 expect(zeroGuard.T).toBe(0);expect(classificationLabel(zeroGuard.class)).toBe('Input handling change');
 const bonus=data.pairs.find(p=>p.pair==='1.4.9->1.5.0')!;
 expect(bonus.T).toBe(0);expect(bonus.S).toBe(35);expect(classificationLabel(bonus.class)).toBe('Scoring-relevant change');
});
it('conditions the no-observed-differences explanation on an actual recorded zero',()=>{
 const pair=data.pairs[0];expect(pairExplanation(pair)).toContain('No test-outcome differences were observed');
 expect(pairExplanation({...pair,T:1})).not.toContain('No test-outcome differences');
 expect(pairExplanation({...pair,T:undefined} as unknown as Pair)).toContain('were not recorded');
});
it('keeps refactor and no-relevant-change controls visibly distinct',()=>{
 at('Release Explorer','1.4.0->1.4.1');
 expect(screen.getByText('Behavior-preserving refactor',{selector:'.badge'})).toBeTruthy();expect(screen.getByText(/This pair is recorded as a refactor expected/)).toBeTruthy();
 expect(screen.queryByText('No scoring-relevant implementation change was identified for this pair.')).toBeNull();
});
it('renders an observed zero as an explicit result rather than an empty chart',()=>{
 at('Release Explorer');expect(document.body.textContent).not.toMatch(/\bnull\b/);
 expect(screen.getByText(/All recorded measurements are zero/)).toBeTruthy();
 const counts=screen.getByRole('table',{name:'Recorded exposure and changed assessment counts'});expect(within(counts).getAllByRole('cell').map(e=>e.textContent)).toEqual(['0','0','0','0']);
 expect(screen.queryByRole('img',{name:'Recorded exposure and changed assessment counts'})).toBeNull();
});
it('renders missing measurements separately from the zero cells beside them',()=>{
 const copy=structuredClone(data);copy.pairs[0].T=undefined as unknown as number;delete copy.pairs[0].weighted_top1M.T;
 at('Release Explorer','1.3.2->1.3.3',copy);
 expect(screen.getByText(/Test-outcome differences were not recorded/)).toBeTruthy();expect(screen.queryByText(/All recorded measurements are zero/)).toBeNull();
 const counts=screen.getByRole('table',{name:'Recorded exposure and changed assessment counts'});
 expect(within(counts).getAllByRole('cell').map(e=>e.textContent)).toEqual(['0','Not recorded','0','0']);
 expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0);
});
it('retains zero percentage and interval values while clearly marking missing inputs',()=>{
 expect(fmt(0)).toBe('0');expect(fmt(undefined)).toBe('Not recorded');expect(percentage(0,16264)).toBe(0);expect(percentage(undefined,16264)).toBeNull();
 const view=render(<IntervalText value={{pct:0,ci95:[0,0]}}/>);expect(screen.getByText(/0.0000%/)).toBeTruthy();view.rerender(<IntervalText/>);expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0);
});
it('does not turn an absent or unqualified empty table into a claim of no change',()=>{
 const view=render(<Table rows={undefined} label="Missing outcomes"/>);expect(screen.getByText('Not recorded')).toBeTruthy();view.rerender(<Table rows={{}} label="Missing outcomes"/>);expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0);
});
it('selects all 26 release pairs with readable labels and shareable original identifiers',()=>{
 at('Release Explorer');const select=screen.getByRole('combobox',{name:'Release pair'});expect(within(select).getAllByRole('option')).toHaveLength(26);
 for(const pair of data.pairs){
  expect(within(select).getByRole('option',{name:`${pair.pair.replace('->',' → ')} · ${classificationLabel(pair.class)}`})).toBeTruthy();
  fireEvent.change(select,{target:{value:pair.pair}});expect(screen.getByRole('heading',{level:2,name:pair.pair.replace('->',' → ')})).toBeTruthy();expect(new URLSearchParams(location.hash.slice(2)).get('pair')).toBe(pair.pair);
 }
});
it('uses the same readable options in Mechanisms and Remediation Plans',()=>{
 for(const view of ['Mechanisms','Remediation Plans']){
  at(view);const select=screen.getByRole('combobox',{name:'Release pair'});expect(within(select).getAllByRole('option')).toHaveLength(26);expect(select.textContent).not.toMatch(/\bnull\b| · refactor\b| · defensive\b| · scoring\b/);cleanup();
 }
});
it('does not mutate original classifications, evidence locations or scientific measurements',()=>{
 const before=JSON.stringify(data);
 for(const pair of data.pairs){classificationLabel(pair.class);classificationMeaning(pair.class);pairExplanation(pair);}
 for(const entry of data.manifest){manuscriptLocation(entry);if(entry.figure)figureDescription(entry.figure);}
 expect(JSON.stringify(data)).toBe(before);expect(data.manifest.find(x=>x.id==='plans')?.manuscript_location).toBe('§5.4; Figure 3');
});
it('loads the supplied hash selection directly with its original identifier',()=>{
 at('Overview','1.5.2->1.5.3');fireEvent.click(screen.getByRole('navigation').querySelector('a[href*="Release%20Explorer"]')!);
 expect((screen.getByRole('combobox',{name:'Release pair'}) as HTMLSelectElement).value).toBe('1.5.2->1.5.3');
});
it('distinguishes the pipeline, two numerical manuscript figures and supplementary plots',()=>{
 expect(catalogue.figures.map(f=>f.number)).toEqual([1,2,3]);expect(catalogue.figures[0].kind).toBe('methodological diagram');expect(catalogue.figures[0].generated_assets).toEqual([]);
 expect(figureDescription('figures/fig_cascade.pdf')).toMatch(/^Figure 2/);expect(figureDescription('figures/fig_remediation_plan_failures.pdf')).toMatch(/^Figure 3/);expect(figureDescription('figures/fig_margin_companion.pdf')).toContain('Supplementary');
});
it('shows corrected evidence locations while retaining working original downloads',()=>{
 at('Artifact');const plan=screen.getByRole('heading',{name:/125 distinct websites/}).closest('article')!;
 expect(within(plan).getByText('§5.4; Figure 3')).toBeTruthy();expect(within(plan).getByRole('link',{name:'Regenerated public figure ↓'}).getAttribute('href')).toBe('./figures/fig_remediation_plan_failures.pdf');
 expect(screen.getByRole('link',{name:'Figure correspondence ↓'}).getAttribute('href')).toBe('./data/figure-references.json');expect(screen.getByRole('link',{name:'Download verified scientific archive ↓'}).getAttribute('href')).toBe('./downloads/scientific-artifact.zip');
});

it('introduces the research without a manuscript download and offers curated reproducibility documents',()=>{
 at('Overview');expect(document.querySelector('a[href*="paper/"]')).toBeNull();cleanup();
 at('Artifact');expect(screen.queryByRole('heading',{name:'Authoritative manuscript'})).toBeNull();
 expect(screen.getByRole('heading',{name:'Evidence and reproducibility'})).toBeTruthy();
 for(const name of ['REPRODUCIBILITY','METHODS_AND_LIMITATIONS','EVIDENCE_MAP','FIGURES'])expect(document.querySelector(`a[href="./docs/${name}.md"]`)).toBeTruthy();
 expect(document.querySelector('a[href*="paper/"]')).toBeNull();
});

it('keeps an empty recorded restoration table distinct from missing restoration details',()=>{
 const plan={eligible:10,fate:{every_fails:0,some_fail:0,none_fail:10},category:{identical:10},additional_effort_min:{},action_count_transitions:{}};
 const view=render(<PlanDetails plan={plan}/>);expect(screen.getByText(/No failing plans were observed under this pair/)).toBeTruthy();expect(screen.getByText(/No changed minimum-plan families were observed/)).toBeTruthy();
 view.rerender(<PlanDetails plan={{...plan,additional_effort_min:undefined,category:{}}}/>);expect(screen.queryByText(/No changed minimum-plan families were observed/)).toBeNull();expect(screen.queryByText(/No failing plans were observed under this pair/)).toBeNull();expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0);
});
