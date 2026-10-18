---
icon: scale-balanced
---

# declared_vs_detected.py

> Puts what a corpus's build *declares* — the dialect written into `TEXT/@dialect` and the source orthography named in `generate_xml.sh` — beside what the dialect detector and the orthography detector *find* in the text, one table per question. Evidence for a port audit; never a gate.

## What it's for

A build declares its dialect and its source orthography in two or three places (the XML attribute, the `--orthography` or conversion-table flag, the README), and a wrong declaration produces a well-formed corpus that validates cleanly. This script is the cross-check: it runs the two detectors and prints every disagreement as a `MISMATCH` row for a human to judge.

## How it works

- **Dialect.** For each XML file with a trained model for its language (`QC/utilities/dialect_models/`: Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, Seediq/Truku as of October 2026) it runs [dialect_detector](dialect-detector.md) on the standard tier and counts `(xml:lang, declared, detected)` triples. `unknown` means the detector was below its commitment threshold; `(no verdict)` means no model or no standard tier.
- **Orthography.** It reads the declared source orthography from `--generate-xml` (`--orthography <name>`, or the `<Source>` part of a `<Lang>_<Source>_113.tsv` conversion table; `94` is Ortho94) unless `--declared-orthography` is given, then runs [orthography_detector.py](orthography-detector.md) twice: original tier against the declaration, standard tier against `Ortho113`, files pooled per declared dialect. Each row shows the best match, its score, the unexpected-letter percentage and the two runners-up.

## Usage

```bash
source .venv/bin/activate
python QC/validation/declared_vs_detected.py \
    --xml Corpora/<Corpus>/XML \
    --generate-xml Corpora/<Corpus>/CodeAndDocs/generate_xml.sh
# when the build script keeps the table in a shell variable:
python QC/validation/declared_vs_detected.py --xml Corpora/<Corpus>/XML --declared-orthography Ortho94
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `--xml` | required | Published XML directory (CodeAndDocs snapshots are skipped). |
| `--generate-xml` | none | Build script to read the declared source orthography from. |
| `--declared-orthography` | none | The declaration itself; overrides `--generate-xml`. |
| `--models_dir` / `--orthographies` | repo defaults | Where the dialect models / orthography tables live. |
| `--skip-dialect` / `--skip-orthography` | off | Run only one half. |

## Output & side effects

Read-only; always exits 0. Three tables on stdout:

```
== Dialect: declared (TEXT/@dialect) vs detected (dialect_detector, standard tier) ==
xml:lang declared        detected         files  note
ami      Coastal         Coastal             12  agree
ami      Coastal         Southern             2  MISMATCH
dialect mismatches: 2 file(s)

declared source orthography: Ortho94  [--tsv_path …/Amis_94_113.tsv]
== Orthography, original tier: declared source orthography vs detected (orthography_detector) ==
group            files  declared    detected     score unexpected%  note
Coastal             14  Ortho94     Ortho94       0.97         0.3  agree  (next: Ortho113 0.95, Church 0.80)
orthography mismatches (original): 0 group(s)
```

A `MISMATCH` row is a question for the maintainer, not a defect to fix: the detectors are statistical, a corpus can legitimately mix sources, and the dialect models cover seven languages.

## When to run it

In the port skill after the port-readiness gate, and in a dev-repo audit after the validators; quote the tables in the summary.

## Related

- [dialect_detector](dialect-detector.md)
- [orthography_detector.py](orthography-detector.md)
- [validate_dialect.py](validate-dialect.md) — the plain `(xml:lang, dialect)` count table
- [Porting a Corpus In](../porting-a-corpus.md)
