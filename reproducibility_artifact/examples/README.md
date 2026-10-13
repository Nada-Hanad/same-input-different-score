# Level 2 — synthetic real-scorer replay

Requires Node 24.21.0+ and npm. Run from reproducibility_artifact:

    node examples/install.mjs
    node examples/run.mjs

Installation requires npm-registry access. The replay itself is offline: the original retriever is replaced by the stored-input stub, and HTTP, HTTPS, fetch, socket, TLS and DNS calls are denied. Scoring tests, modifiers and grading execute inside each genuine historical package. Four exact release versions and their transitive integrity locks are included; node_modules is not included.

An optional external environment root keeps installations outside the artifact:

    node examples/install.mjs /tmp/observatory-example-env
    node examples/run.mjs /tmp/observatory-example-env

Two public synthetic fixtures are included:

- 1.4.9 → 1.5.0: identical test outcomes, X-Frame-Options modifier 0 → +5, displayed score 120 → 125 (both A+).
- 1.5.2 → 1.5.3: the HTTPS base resolves a protocol-relative external script under jsdom. The real SRI outcome changes from external scripts loaded securely to not loaded securely; modifier −5 → −50; score 65/B− → 20/F.

For the parser fixture, all 512 nine-action subsets are scored under both releases. The two tied one-action B plans are CSP and content-type options; both fail under the newer release and no subset reaches B. expected.json contains the actually executed old/new outcomes, modifiers, scores, grades, uncurved scores and plan outputs. run.mjs asserts them automatically. --record is a maintainer-only command for recording newly inspected fixture outputs; normal reproduction never updates expected outputs.

Inputs use .invalid hosts, synthetic HTML, and an empty cookie jar. No collected response, credential, private corpus row or real website is needed. The synthetic empty HSTS/TLD lists deliberately differ from empirical-study references. This demonstration confirms controlled scorer-level behavior; it does not reproduce corpus counts, establish actual deployment safety, or explain every empirical changed website.

## Unchanged original score, failing plan

The third fixture is deliberately constructed from the parser example: omit protective headers, keep an HTTP response without redirection, and add one artificial sessionid cookie with value synthetic-only under fixture.invalid. Real scorers display0/0 with uncurved−35/−80. Complete enumeration finds one three-action old minimum B plan, CSP+HSTS+cookie flags, scoring70→25. Maximum newer score30. CSP also supplies frame-ancestors, so three actions suffice; the initial four-action anticipation was rejected by exhaustive execution. This is a controlled synthetic phenomenon, not a reproduction of private website counts. `node examples/run.mjs` asserts all three fixtures. The exact outputs are flooring-expected.json; fixture input is flooring-input.json.
