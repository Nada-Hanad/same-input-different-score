# Source and dependency notice

input_codec.mjs and stub_retriever.mjs are unchanged research-harness copies from audit/scripts/observatory_replay. worker.mjs adapts the module hook and result projection of replay_all.mjs. run.mjs adapts the modeled input transformations of remediate.mjs. The genuine scorer packages are installed separately from the npm registry using exact pinned lockfiles; no cached dependency or scorer source tree is redistributed in the ZIP.

The four Observatory packages declare MPL-2.0. Retained lock manifests record transitive package versions, integrity hashes, and license metadata. npm ci --ignore-scripts avoids native/retriever postinstall work. Synthetic empty HSTS/TLD lists are written only into the isolated example environments. They are not the study's historical lists.

The research harness has no project-wide redistribution license recorded. The user's instruction authorizes this local anonymous-review artifact; an explicit project license must be selected before general public code redistribution. No new license is inferred or assigned here. Original author-identifying Git metadata is excluded.
