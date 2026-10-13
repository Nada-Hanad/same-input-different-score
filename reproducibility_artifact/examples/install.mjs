// Optional dependency installation. Network is required here, never during fixture execution.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const [nodeMajor,nodeMinor]=process.versions.node.split('.').map(Number);
if(nodeMajor<24||(nodeMajor===24&&nodeMinor<21))throw Error('Use the documented Node24.21.0 environment; current Node is too old. No installation will be attempted.');
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(process.argv[2]??path.join(here,'environments'));
for(const version of ['1.4.9','1.5.0','1.5.2','1.5.3']){
 const dir=path.join(root,version);fs.mkdirSync(dir,{recursive:true});
 for(const name of ['package.json','package-lock.json']){const from=path.join(here,'environments',version,name),to=path.join(dir,name);if(from!==to)fs.copyFileSync(from,to);}
 const npm=process.platform==='win32'?'npm.cmd':'npm';
 const p=spawnSync(npm,['ci','--ignore-scripts','--no-audit','--no-fund'],{cwd:dir,stdio:'inherit'});
 if(p.status!==0)throw Error(`Dependency installation failed for ${version}`);
 // Synthetic fixture references: .invalid hosts are deliberately not HSTS-preloaded.
 // No historical reference data is copied or downloaded. Scorer source remains unchanged.
 const conf=path.join(dir,'node_modules/@mdn/mdn-http-observatory/conf');fs.mkdirSync(conf,{recursive:true});
 fs.writeFileSync(path.join(conf,'hsts-preload.json'),'{}\n');fs.writeFileSync(path.join(conf,'tld-list.json'),'[]\n');
}
console.log('Installed four exact, locked scorer environments with synthetic reference lists. Run run.mjs with the same environment root.');
