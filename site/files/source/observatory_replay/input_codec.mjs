// Store and rebuild the input an Observatory release scores, so any release can score it offline.
//
// The fields kept are exactly those the analyzers of releases 1.3.2 to 1.7.1 read, established by
// reading every analyzer, the scanner and the grader of all 27 releases (PREREGISTRATION_2026-09-27,
// section 3): the four responses with status, headers and the `verified` flag; the `auto` response's
// http-equiv map; both redirect chains; the page body; the session URL and its cookie jar; and the
// CORS response's request headers, which the CORS test reads. The collector checks the codec on
// every site by scoring the rebuilt input and requiring an exact match with the in-memory result.
//
// Releases up to 1.3.8 construct their input from a hostname string and read `requests.hostname`;
// later ones read `requests.site`. The rebuilt object carries both, which is what lets one stored
// input serve every release.

const RESPONSES = ["auto", "http", "https", "cors"];

function packResponse(resp) {
  if (!resp) return null;
  const headers = typeof resp.headers?.toJSON === "function" ? resp.headers.toJSON() : { ...(resp.headers ?? {}) };
  const reqHeaders = resp.request?.headers;
  return {
    status: resp.status ?? null,
    statusText: resp.statusText ?? "",
    headers,
    verified: resp.verified ?? false,
    httpEquiv: resp.httpEquiv instanceof Map ? [...resp.httpEquiv.entries()] : null,
    requestHeaders: reqHeaders && typeof reqHeaders === "object" ? { ...reqHeaders } : null,
    hasRequest: resp.request !== undefined && resp.request !== null,
  };
}

const packChain = (chain) => (chain ?? []).map((e) => ({ url: e.url?.href ?? String(e.url), status: e.status }));

/** @returns {object} a JSON-safe copy of a `Requests` object */
export function pack(requests) {
  const responses = {};
  for (const k of RESPONSES) responses[k] = packResponse(requests.responses?.[k]);
  // `auto` is always the same object as `http` or `https`; record which, so identity survives
  for (const k of ["https", "http"]) {
    if (requests.responses?.auto && requests.responses.auto === requests.responses[k]) responses.autoIs = k;
  }
  const site = requests.site ?? { hostname: requests.hostname };
  return {
    site: { hostname: site.hostname, port: site.port ?? null, path: site.path ?? null },
    httpPort: requests.httpPort ?? null,
    httpsPort: requests.httpsPort ?? null,
    responses,
    httpRedirects: packChain(requests.responses?.httpRedirects),
    httpsRedirects: packChain(requests.responses?.httpsRedirects),
    body: requests.resources?.path ?? null,
    session: requests.session
      ? { url: requests.session.url?.href ?? null, jar: requests.session.jar?.serializeSync?.() ?? null }
      : null,
  };
}

function unpackResponse(p, AxiosHeaders) {
  if (!p) return null;
  const resp = {
    status: p.status,
    statusText: p.statusText,
    headers: AxiosHeaders.from(p.headers),
    verified: p.verified,
  };
  if (p.httpEquiv) resp.httpEquiv = new Map(p.httpEquiv);
  if (p.hasRequest) resp.request = p.requestHeaders ? { headers: { ...p.requestHeaders } } : {};
  return resp;
}

/**
 * Rebuild a `Requests`-shaped object from `pack()` output.
 * @param {object} p packed input
 * @param {{ AxiosHeaders: any }} deps the AxiosHeaders class to wrap headers in
 */
export function unpack(p, { AxiosHeaders }) {
  const responses = {};
  for (const k of RESPONSES) responses[k] = unpackResponse(p.responses[k], AxiosHeaders);
  if (p.responses.autoIs) responses.auto = responses[p.responses.autoIs];
  responses.httpRedirects = p.httpRedirects.map((e) => ({ url: new URL(e.url), status: e.status }));
  responses.httpsRedirects = p.httpsRedirects.map((e) => ({ url: new URL(e.url), status: e.status }));
  const site = { hostname: p.site.hostname, port: p.site.port ?? undefined, path: p.site.path ?? undefined };
  const jar = p.session?.jar ?? null;
  return {
    site,
    hostname: p.site.hostname,
    httpPort: p.httpPort ?? site.port ?? 80,
    httpsPort: p.httpsPort ?? site.port ?? 443,
    resources: { path: p.body },
    responses,
    session: p.session
      ? {
          url: p.session.url ? new URL(p.session.url) : null,
          jar: { serializeSync: () => (jar ? structuredClone(jar) : { cookies: [] }) },
        }
      : null,
  };
}

/** The comparable part of a scan result: score, grade and each test's outcome. */
export function summarize(result) {
  const tests = {};
  for (const [name, t] of Object.entries(result.tests ?? {})) tests[name] = t?.result ?? null;
  return { score: result.scan.score, grade: result.scan.grade, tests };
}

export function sameSummary(a, b) {
  if (a.score !== b.score || a.grade !== b.grade) return false;
  const keys = new Set([...Object.keys(a.tests), ...Object.keys(b.tests)]);
  for (const k of keys) if (a.tests[k] !== b.tests[k]) return false;
  return true;
}
