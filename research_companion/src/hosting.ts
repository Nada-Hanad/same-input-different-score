// Relative resources and fragment navigation also work in opaque-origin sandboxes.
export function routeSearch() {
  return location.hash.startsWith('#?') ? location.hash.slice(1) : location.search;
}
export function routeUrl() {
  const u = new URL(location.href);
  u.search = routeSearch();
  u.hash = '';
  return u;
}
export function writeRoute(u: URL, replace = true) {
  const hash = '#' + u.search;
  if (location.hash === hash) return;
  try { history[replace ? 'replaceState' : 'pushState'](null, '', hash); }
  catch { if(replace) location.replace(hash); else location.hash = hash; }
  window.dispatchEvent(new Event('artifact-route'));
}
export function resource(path: string) {
  if (/^https?:\/\//.test(path)) return path;
  const root = document.querySelector<HTMLMetaElement>('meta[name="artifact-root"]')?.content ?? './';
  return root + path.replace(/^\//, '');
}
export function storedTheme() { try {return localStorage.getItem('theme') === 'dark';} catch {return false;} }
export function storeTheme(dark: boolean) { try {localStorage.setItem('theme', dark?'dark':'light');} catch {/* optional preference only */} }
const loads = new Map<string, Promise<unknown>>();
export function loadData(name: 'core'|'population'): Promise<any> {
  const entry = name === 'core' ? 'research-core' : 'population';
  if(!loads.has(name)) loads.set(name,new Promise((resolve,reject)=>{
    const script=document.createElement('script');script.src=resource(`data/${entry}.js`);
    script.onload=()=>{const data=(window as any).__artifactData?.[name];data?resolve(data):reject(Error('Research data unavailable'));};
    script.onerror=()=>{loads.delete(name);reject(Error('Research dataset could not be loaded'));};
    document.head.append(script);
  }));
  return loads.get(name)!;
}
export function opaqueOrigin() {return window.origin === 'null';}
