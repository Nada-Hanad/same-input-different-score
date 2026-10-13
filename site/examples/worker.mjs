// Adapted from audit/scripts/observatory_replay/replay_all.mjs; scoring code is unchanged.
import fs from 'node:fs';
import path from 'node:path';
import {registerHooks,syncBuiltinESMExports} from 'node:module';
import {pathToFileURL} from 'node:url';
import {unpack} from './lib/input_codec.mjs';
// Fail closed if any code tries to open a network connection, including loopback.
let attempts=0;
const deny=()=>{attempts++;throw Error('Network access blocked by synthetic replay harness');};
for(const name of ['node:http','node:https']){const m=await import(name);m.default.request=deny;m.default.get=deny;}
const net=(await import('node:net')).default;net.connect=deny;net.createConnection=deny;net.Socket.prototype.connect=deny;
const tls=(await import('node:tls')).default;tls.connect=deny;
const dns=(await import('node:dns')).default;dns.lookup=deny;dns.resolve=deny;
globalThis.fetch=deny;syncBuiltinESMExports();
const [pkgDir,inputPath]=process.argv.slice(2);
const stub=new URL('./lib/stub_retriever.mjs',import.meta.url).href;
registerHooks({resolve(specifier,context,nextResolve){const r=nextResolve(specifier,context);return r.url.includes('/@mdn/mdn-http-observatory/src/retriever/retriever.js')?{...r,url:stub,shortCircuit:true}:r;}});
const src=path.join(pkgDir,'node_modules/@mdn/mdn-http-observatory/src');
const {scan}=await import(pathToFileURL(path.join(src,'scanner/index.js')).href);
const {AxiosHeaders}=await import(pathToFileURL(path.join(pkgDir,'node_modules/axios/index.js')).href);
const input=JSON.parse(fs.readFileSync(inputPath,'utf8'));
const inputs=Array.isArray(input)?input:[input];const out=[];
for(const packed of inputs){
 globalThis.__OBS_STORED_INPUT__=unpack(packed,{AxiosHeaders});
 const r=await scan({hostname:packed.site.hostname});
 const tests={},mods={};let uncurved=100,extra=0;
 for(const [name,t] of Object.entries(r.tests)){tests[name]=t.result;mods[name]=t.scoreModifier;if(t.scoreModifier<0)uncurved+=t.scoreModifier;else extra+=t.scoreModifier;}
 out.push({score:r.scan.score,grade:r.scan.grade,algorithm_version:r.scan.algorithmVersion,uncurved,extra,tests,mods});
 globalThis.__OBS_STORED_INPUT__=undefined;
}
if(attempts!==0)throw Error(`Unexpected network attempts: ${attempts}`);
console.log(JSON.stringify({network_attempts:attempts,results:out}));
