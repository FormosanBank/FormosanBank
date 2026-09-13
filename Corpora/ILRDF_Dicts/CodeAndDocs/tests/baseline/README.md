# Baseline for the v2 rework

The v2 rework is judged against PR #179's committed XML (`963d1579e`).
Recreate any baseline file with:

    git show 963d1579e:Corpora/ILRDF_Dicts/XML/<Lang>/<Lang>.xml

## PR #179 inventory, verified 2026-09-05

| | |
|---|---:|
| files | 16 |
| `S` | 167,821 |
| `FORM[@kindOf="original"]` | 167,821 |
| `FORM[@kindOf="standard"]` | 167,821 |
| `PHON` | 167,821 |
| `TRANSL` | 169,946 |
| `AUDIO` | 132,402 |

These match `CodeAndDocs/docs/qc_report.md`, so the committed XML is what that
report describes.

Every count change from this baseline must be explained in the QC report's
change-classification table. See
`docs/superpowers/plans/2026-09-05-ilrdf-dicts-v2.md`, Task 10.
