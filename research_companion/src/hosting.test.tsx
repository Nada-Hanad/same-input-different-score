import React from 'react';
import {afterEach, expect, it, vi} from 'vitest';
import {act, cleanup, fireEvent, render, screen} from '@testing-library/react';
import {routeSearch, routeUrl, writeRoute, resource, storedTheme, storeTheme, loadData} from './hosting';
import {download} from './model';
import {App} from './main';
import source from '../../reproducibility_artifact/data/research.json';
import type {Research} from './model';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();history.replaceState(null,'','/');document.querySelector('meta[name="artifact-root"]')?.remove();});
it('prefers a shared fragment route over legacy query parameters',()=>{
 history.replaceState(null,'','/REPOSITORY/?view=Overview#?view=Mechanisms&pair=1.5.2-%3E1.5.3');
 expect(routeSearch()).toContain('view=Mechanisms');
 expect(routeUrl().searchParams.get('pair')).toBe('1.5.2->1.5.3');
});
it('retains legacy query links when no fragment route is present',()=>{
 history.replaceState(null,'','/REPOSITORY/?view=Artifact');expect(routeSearch()).toBe('?view=Artifact');
});
it('writes shareable routes without escaping the project prefix',()=>{
 history.replaceState(null,'','/REPOSITORY/');const u=routeUrl();u.searchParams.set('view','Release Explorer');writeRoute(u,false);
 expect(location.pathname).toBe('/REPOSITORY/');expect(location.hash).toBe('#?view=Release+Explorer');
});
it('resolves site and root bridge resources without hardcoded repository names',()=>{
 expect(resource('/docs/REPRODUCIBILITY.md')).toBe('./docs/REPRODUCIBILITY.md');
 const meta=document.createElement('meta');meta.name='artifact-root';meta.content='./site/';document.head.append(meta);
 expect(resource('/data/population.js')).toBe('./site/data/population.js');expect(resource('https://developer.mozilla.org/')).toBe('https://developer.mozilla.org/');
});
it('continues when the sandbox denies storage access',()=>{
 vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw new DOMException('Denied','SecurityError');});
 vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new DOMException('Denied','SecurityError');});
 expect(storedTheme()).toBe(false);expect(()=>storeTheme(false)).not.toThrow();
});
it('loads deferred data as a same-path classic script, without fetch',async()=>{
 const fetchSpy=vi.spyOn(window,'fetch');const pending=loadData('population');
 const script=document.querySelector<HTMLScriptElement>('script[src="./data/population.js"]')!;expect(script).toBeTruthy();expect(script.type).toBe('');
 (window as any).__artifactData={population:{population:{levels:{verified:true}}}};script.dispatchEvent(new Event('load'));
 expect(await pending).toEqual({population:{levels:{verified:true}}});expect(fetchSpy).not.toHaveBeenCalled();script.remove();
});
it('offers copyable filtered JSON when an opaque hosting origin blocks downloads',()=>{
 vi.stubGlobal('origin','null');window.scrollTo=vi.fn();render(<App data={source as unknown as Research}/>);
 act(()=>download('filtered.json',{safe:true}));const box=screen.getByRole('textbox',{name:'Filtered JSON to copy'}) as HTMLTextAreaElement;
 expect(JSON.parse(box.value)).toEqual({safe:true});expect(document.activeElement).toBe(box);fireEvent.keyDown(box,{key:'Escape'});expect(screen.queryByRole('dialog')).toBeNull();
});
it('opens a shared fragment directly into the selected research section',()=>{
 history.replaceState(null,'','/REPOSITORY/#?view=Mechanisms&pair=1.5.2-%3E1.5.3&target=B');window.scrollTo=vi.fn();render(<App data={source as unknown as Research}/>);
 expect(screen.getByRole('heading',{level:1,name:'Mechanisms'})).toBeTruthy();
});
