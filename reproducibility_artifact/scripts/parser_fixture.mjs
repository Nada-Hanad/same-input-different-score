// Synthetic parser mechanism check, no network request and no empirical score claim.
// node parser_fixture.mjs <old-package-directory> <new-package-directory>
// Each directory must contain node_modules/jsdom or node_modules/htmlparser2 respectively.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const [oldDir,newDir]=process.argv.slice(2);
if(!oldDir||!newDir)throw Error('Provide the old and new installed-package directories. See docs/REPRODUCIBILITY.md.');
const oldRequire=createRequire(path.join(path.resolve(oldDir),'package.json'));
const newRequire=createRequire(path.join(path.resolve(newDir),'package.json'));
const {JSDOM}=oldRequire('jsdom');const {Parser}=newRequire('htmlparser2');
const input=fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)),'../fixtures/parser-input.html'),'utf8');
const dom=new JSDOM(input,{url:'https://fixture.invalid/'});
const resolved=dom.window.document.querySelector('script').src;
let raw;
const parser=new Parser({onopentag(name,attrs){if(name==='script')raw=attrs.src;}});parser.write(input);parser.end();
assert.equal(resolved,'https://cdn.fixture.invalid/script.js');
assert.equal(raw,'//cdn.fixture.invalid/script.js');
dom.window.close();
console.log(JSON.stringify({status:'passed',kind:'synthetic parser mechanism fixture',jsdom_resolved:resolved,htmlparser2_raw:raw,network_requests:0,limitation:'Not an empirical website replay or a complete scoring comparison.'},null,2));
