# GitHub Copilot Content Exclusion

Repository files alone cannot fully configure GitHub Copilot organization content exclusion. This must be set in GitHub organization or repository settings by an account with the required permissions.

## Recommended Exclusions

Exclude at minimum:

```text
Corpora/**
Orthographies/**
statistics/**
**/*.xml
**/*.csv
**/*.tsv
**/*.jsonl
**/*.parquet
**/*.wav
**/*.mp3
**/*.flac
```

## Rationale

These paths contain corpus data, corpus-derived data, exports, metrics, audio references, and files that should not be used as Copilot context.

This does not stop all public web scraping or all AI training. It reduces Copilot access where GitHub's content-exclusion controls apply and adds evidence that FormosanBank reserved these uses.

## Repo-Level Signals Added Here

This repository also includes:

- `AI-USE-ADDENDUM.md`
- `NOTICE-AI.md`
- `LICENSE.md`
- `.github/copilot-instructions.md`

These files are notice and instruction signals. They are not a substitute for the GitHub settings-level content exclusion above.
