// Remediation search only: stands in for `jsdom` inside an Observatory release so that the page body,
// which no header action changes, is parsed once per site instead of once per action set. It returns
// the real JSDOM object built by the release's own jsdom; the SRI test only reads from it. Equality
// with the unmemoised replay is checked on every site's base input by remediate.mjs.
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// loaded by absolute path, which the redirecting hook in remediate.mjs does not intercept
const real = new URL(import.meta.url).searchParams.get("real");
const Real = createRequire(import.meta.url)(fileURLToPath(real)).JSDOM;
let lastHtml, lastDom, lastError;

export function JSDOM(html, options) {
  if (options === undefined && html === lastHtml) {
    // a page jsdom cannot parse throws the same error on every subset; the SRI test only catches
    // it, so rethrowing the first error is the same outcome without re-parsing the page each time
    if (lastError) throw lastError;
    if (lastDom) return lastDom;
  }
  let dom;
  try {
    dom = new Real(html, options);
  } catch (e) {
    if (options === undefined) remember(html, undefined, e);
    throw e;
  }
  if (options === undefined) remember(html, dom, undefined);
  return dom;
}

function remember(html, dom, error) {
  // Releases up to 1.5.2 never close the window they open, so memory grows by one window per
  // site. Once the next site is parsed the previous window is never read again, so close it.
  try { lastDom?.window.close(); } catch { /* already closed */ }
  lastHtml = html;
  lastDom = dom;
  lastError = error;
}
