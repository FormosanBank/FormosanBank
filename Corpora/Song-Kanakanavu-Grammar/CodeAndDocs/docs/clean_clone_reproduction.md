# Clean-clone reproduction

Private `main` commit `5361d797ae4833ae278c255e3ad1103cb670cb34` was cloned into an empty temporary directory. The rebuild used the clean, pinned FormosanBank validator checkout at `a20f81b470ed141c12425f3d827227b22d9f9ece` through an explicit `FORMOSANBANK_PATH`.

The clean clone regenerated the dictionary and interlinear ledgers and both XML files byte-for-byte. It applied 128 exact direct-sentence decisions and two exact analysis-tier decisions, emitted 140 dictionary alternates, omitted the unsupported standard tier for all 11 bound dictionary citation forms, folded source stress outside original tiers, and delegated both PHON tiers to the shared Ortho113 utility.

Reproduced hashes:

| Artifact | SHA-256 |
|---|---|
| Grammar XML | `3b79637d62576b8ad66b7f7ea765a83583b1d28d91a67fb6fe3a07624779a543` |
| Dictionary XML | `dc6c58f0d3ed98a3c6f1eddfab10175c34cf53e4eb348610a7ef0d00ad8f6324` |
| Exact decision manifest | `b3d94c4fff5e1b0af3e8eb14f8aab022f5780164900a61bf8260a98bc2333914` |

All 17 regression tests passed in the clean clone. The rebuilt clone had no tracked or untracked changes. The pinned FormosanBank checkout also remained clean.

Canonical validation of these exact XML hashes reported zero hard XML, text, or gloss findings. Full findings and adjudication are retained in `qc-output/20260806T033701Z_goal_completion/`.

The Basecamp evidence records the author's (Li-May Sung's) permission to publish this corpus under CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial).
