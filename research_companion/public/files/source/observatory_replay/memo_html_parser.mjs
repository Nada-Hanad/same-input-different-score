// Remediation search only: memoises collectElements() of a release's src/utils/html-parser.js by
// its arguments, for the same reason as memo_jsdom.mjs. The other exports pass through unchanged.
const realUrl = new URL(import.meta.url).searchParams.get("real");
const real = await import(`${realUrl}?unmemoised`);
let lastHtml, lastTag, lastOut;

export function collectElements(html, tagName) {
  if (lastOut !== undefined && html === lastHtml && tagName === lastTag) return lastOut;
  lastOut = real.collectElements(html, tagName);
  lastHtml = html;
  lastTag = tagName;
  return lastOut;
}
export const getAttribute = real.getAttribute;
export const hasAttribute = real.hasAttribute;
