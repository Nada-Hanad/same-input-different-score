// Genuine historical assessment-code execution on synthetic inputs; not corpus reproduction.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const [nodeMajor,nodeMinor]=process.versions.node.split('.').map(Number);
if(nodeMajor<24||(nodeMajor===24&&nodeMinor<21))throw Error('Use the documented Node24.21.0 environment; current Node is too old. No installation will be attempted.');
const here=path.dirname(fileURLToPath(import.meta.url));
const envRoot=path.resolve(process.argv[2]??path.join(here,'environments'));
const actions=JSON.parse(fs.readFileSync(path.join(here,'action-definitions.json'),'utf8'));
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'synthetic-observatory-'));
const read=name=>JSON.parse(fs.readFileSync(path.join(here,name),'utf8'));
function score(version,input){
 const lock=JSON.parse(fs.readFileSync(path.join(envRoot,version,'package-lock.json'),'utf8'));
 const pkg=JSON.parse(fs.readFileSync(path.join(envRoot,version,'node_modules/@mdn/mdn-http-observatory/package.json'),'utf8'));
 assert.equal(pkg.version,version);assert.equal(pkg.license,'MPL-2.0');
 const file=path.join(temp,'input.json');fs.writeFileSync(file,JSON.stringify(input));
 const p=spawnSync(process.execPath,[path.join(here,'worker.mjs'),path.join(envRoot,version),file],{encoding:'utf8',maxBuffer:10*1024*1024,timeout:120000});
 if(p.status!==0)throw Error(`Scorer ${version} failed: ${p.stderr}`);
 const d=JSON.parse(p.stdout);assert.equal(d.network_attempts,0);return d.results;
}
function apply(input,mask){
 const p=structuredClone(input),key=p.responses.autoIs??'auto';
 for(let i=0;i<actions.length;i++)if(mask&(1<<i)){
  const a=actions[i];
  if(a.id==='cookies'){for(const c of p.session?.jar?.cookies??[]){c.secure=true;c.httpOnly=true;c.sameSite='strict';}}
  else{for(const h of Object.keys(p.responses[key].headers))if(h.toLowerCase()===a.header)delete p.responses[key].headers[h];p.responses[key].headers[a.header]=a.value;}
 }
 return p;
}
function names(mask){return actions.filter((_,i)=>mask&(1<<i)).map(a=>a.id);}
try{
 const rule=read('rule-input.json'),oldRule=score('1.4.9',rule)[0],newRule=score('1.5.0',rule)[0];
 assert.equal(oldRule.score,120);assert.equal(newRule.score,125);assert.equal(oldRule.mods['x-frame-options'],0);assert.equal(newRule.mods['x-frame-options'],5);assert.deepEqual(oldRule.tests,newRule.tests);
 const parser=read('parser-input.json'),inputs=Array.from({length:512},(_,mask)=>apply(parser,mask));
 const old=score('1.5.2',inputs),next=score('1.5.3',inputs);assert.equal(old.length,512);assert.equal(next.length,512);
 assert.equal(old[0].score,65);assert.equal(next[0].score,20);
 assert.equal(old[0].tests['subresource-integrity'],'sri-not-implemented-but-external-scripts-loaded-securely');
 assert.equal(next[0].tests['subresource-integrity'],'sri-not-implemented-and-external-scripts-not-loaded-securely');
 assert.equal(old[0].mods['subresource-integrity'],-5);assert.equal(next[0].mods['subresource-integrity'],-50);
 const target=70,min=Math.min(...old.map((r,i)=>r.score>=target?names(i).length:99));
 const tied=old.map((r,i)=>({mask:i,old:r,new:next[i]})).filter(x=>x.old.score>=target&&names(x.mask).length===min);
 assert.equal(min,1);assert.equal(tied.length,2);assert.deepEqual(tied.map(x=>names(x.mask)[0]).sort(),['csp','xcto']);assert(tied.every(x=>x.new.score<target));assert(next.every(x=>x.score<target));
 const output={kind:'synthetic real-scorer replay',network_attempts:0,scoring_rule:{pair:'1.4.9->1.5.0',old:oldRule,new:newRule},parser:{pair:'1.5.2->1.5.3',old:old[0],new:next[0]},plan:{target_grade:'B',target_score:target,subsets_evaluated_per_release:512,minimum_actions:min,tied_minimum_plans:tied.map(x=>({actions:names(x.mask),old:x.old,new:x.new})),every_tied_plan_fails:true,any_new_subset_reaches:false,maximum_new_score:Math.max(...next.map(r=>r.score))},limitations:'Safe synthetic responses, empty synthetic reference lists, pinned installed dependencies; not empirical website reproduction or deployment advice.'};
 const expected=path.join(here,'expected.json');
 if(process.argv.includes('--record'))fs.writeFileSync(expected,JSON.stringify(output,null,2)+'\n');
 else assert.deepEqual(output,JSON.parse(fs.readFileSync(expected,'utf8')));
 // Deliberately constructed flooring fixture: real score zero in both releases.
 const floorInput=read('flooring-input.json');
 const floorInputs=Array.from({length:512},(_,mask)=>apply(floorInput,mask));
 const fo=score('1.5.2',floorInputs),fn=score('1.5.3',floorInputs);
 assert.equal(fo[0].score,0);assert.equal(fn[0].score,0);
 assert.equal(fo[0].uncurved,-35);assert.equal(fn[0].uncurved,-80);
 const fk=Math.min(...fo.map((r,i)=>r.score>=70?names(i).length:99));
 const ft=fo.map((r,i)=>({mask:i,old:r,new:fn[i]})).filter(x=>x.old.score>=70&&names(x.mask).length===fk);
 assert.equal(fk,3);assert(ft.length>0);assert(ft.every(x=>x.new.score<70));
 const flooring={kind:'synthetic unchanged-original-score plan failure',pair:'1.5.2->1.5.3',network_attempts:0,original:{old:fo[0],new:fn[0]},plan:{target_grade:'B',target_score:70,subsets_evaluated_per_release:512,minimum_actions:fk,tied_minimum_plans:ft.map(x=>({actions:names(x.mask),old:x.old,new:x.new})),every_tied_plan_fails:ft.every(x=>x.new.score<70),maximum_new_score:Math.max(...fn.map(r=>r.score)),any_new_subset_reaches:fn.some(r=>r.score>=70)},construction:'Based on parser-input.json: omit protective headers, retain an HTTP response without redirection, and add one explicitly synthetic session cookie. HTTPS base and protocol-relative script remain fixed. All values are artificial, under .invalid; synthetic-only is not a real session value.'};
 const floorExpected=path.join(here,'flooring-expected.json');
 if(process.argv.includes('--record'))fs.writeFileSync(floorExpected,JSON.stringify(flooring,null,2)+'\n');
 else assert.deepEqual(flooring,JSON.parse(fs.readFileSync(floorExpected,'utf8')));
 console.log(JSON.stringify({status:'passed',fixture:'unchanged-original-score',original_displayed:[fo[0].score,fn[0].score],original_uncurved:[fo[0].uncurved,fn[0].uncurved],minimum_actions:fk,tied_plans:ft.length,plan_scores:ft.map(x=>[x.old.score,x.new.score]),maximum_new_score:flooring.plan.maximum_new_score,network_attempts:0}));
 console.log(JSON.stringify({status:'passed',rule_scores:[oldRule.score,newRule.score],parser_scores:[old[0].score,next[0].score],minimum_actions:min,tied_minimum_plans:tied.map(x=>names(x.mask)),plan_scores:tied.map(x=>[x.old.score,x.new.score]),maximum_new_score:output.plan.maximum_new_score,network_attempts:0}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
