// Stands in for src/retriever/retriever.js of any Observatory release during replay. The release's
// own scan() calls retrieve() and scores whatever comes back; this returns the stored input that
// replay_all.mjs placed on globalThis, so no network request is made and no scoring code changes.
export async function retrieve() {
  return globalThis.__OBS_STORED_INPUT__;
}

export function buildRequestHeaders() {
  return { http: [], https: [] };
}
