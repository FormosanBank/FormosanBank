# MT quality review

The four recorded MT-quality findings were reviewed against the tracked source
ledger and generated XML on 2026-08-22.

| Record | Finding | Disposition |
| --- | --- | --- |
| `song-2018-kanakanavu-S0143` | `target_linguistic_analysis` | Repaired. The primary Chinese translation is `我有錢。`; the complete source translation `我有錢。（=我的錢存在）` remains in the `TRANSL/@notes` attribute. |
| `song-2018-kanakanavu-S0149` | `target_linguistic_analysis` | Repaired. The primary Chinese translation is `我沒有錢。`; the complete source translation `我沒有錢。（=我的錢沒有）` remains in the `TRANSL/@notes` attribute. |
| `song-2018-kanakanavu-dictionary-0104` | `extreme_fertility` | Retained. This is a source dictionary definition for `kani`, not a sentence alignment. Its length is valid lexical content. |
| `song-2018-kanakanavu-dictionary-0310` | `extreme_fertility` | Retained. This is a source dictionary definition for `mia'acipi`, not a sentence alignment. Its length is valid lexical content. |

The two translation repairs follow FormosanBank POL-024. They are exact,
source-guarded build decisions with regression coverage. The dictionary rows
remain appropriate for dictionary lookup and can continue to be excluded from
sentence-level MT training by the existing corpus filter.
