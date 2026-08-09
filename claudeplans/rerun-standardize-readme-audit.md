# Rerun standardize/add_phonology — README audit (pre-flight)

Branch `feature/rerun-standardize-phonology` off `feature/shared-source-phonology`.
Goal: rerun `standardize.py` + `add_phonology.py` on each corpus, then audit the
standard-tier FORM and original/standard PHON changes. This audit checks each
corpus README for (a) assumed orthographies and (b) any XML changes made **after**
standardization/phonology (which would make a naive rerun wrong).

## Group 1 — Clear to rerun (orthography known, no post-standardization edits)

| Corpus | standardize | add_phonology |
|---|---|---|
| FormosanBankGitBook | `--copy` | `--orthography Ortho113` |
| Glosbe | per-lang TSV: Amis `Amis_94_113`(Coastal), Atayal `Atayal_Church_113`, Truku `Seediq_94_113`(Truku), Saisiyat `Saisiyat_94_113` | ami: Ortho94/Coastal; tay: Church; trv,xsy: Ortho94 |
| SEALS33 | `--copy` | `--orthography Ortho94` |
| Virginia_Fey_Dictionary | `--copy` | `--orthography Ortho113` |
| Wikipedias | `--copy` | `--orthography Ortho113` (default IPA; dialect unknown) |
| WilangYutasVideos | `--copy` | `--orthography Ortho94` |
| Latham-1862 | `--copy` | none (no phonology by design) |

## Group 2 — Post-standardization edits / bespoke pipeline → RAISE before rerun

| Corpus | Why it blocks a naive rerun |
|---|---|
| **HundredPaiwanStories** | README **explicitly forbids** running standardize/add_phonology over published XML: TSV maps `?→'`, reconflating question-mark punctuation with glottal stop; the undo (`fix_ferrell.py`) is hardcoded to the dev path and won't run here. Also has hand corrections (avanu cascade, M-id renumber). |
| **NTUFormosanCorpus** | 17+ post-standardization repair scripts (steps 4–20: empty-M repair, borrow_segmentation, dedupe ids, remove null symbols, annotation-code removal, gloss-lang fixes, manual corrections, L2 markers, infix conversion, sentence splitting…), several regenerate PHON themselves; plus manual V121 review "must be redone after any regeneration." |
| **ePark** | Post-std fix-ups: `drop_unmapped_phon.py`, `fix_parenthetical_spacing.py`, and a **2nd** `clean_xml.py` pass over the standard tier. Complex per-sub-corpus orthographies (Ortho113 / Ortho113Liberal / Ortho94). |
| **Presidential_Apologies** | Tsou & Kanakanavu Mandarin parentheticals were removed from the **standard** tier but left in **original**. Re-running `--copy` would re-introduce them into standard. |
| **Li-Conjunction-Thao** | Requires `flatten_standard_segmentation.py` **after** standardize (standardize re-introduces `- = < >` markers into standard FORM). |
| **Nowbucyang-Truku-Thesis** | Requires a 2nd `clean_xml.py` (de-segment) **after** standardize. |
| **Safolu-Amis-Dictionary** | `remove_duplicate_sentences.py --apply` runs after phonology, dropping 255 sentences on the standard tier. |
| **Song-Kanakanavu-Grammar** | After `--copy`: `normalize_standard_forms.py` (128 reviewed decisions) + `fold_standard_stress.py`; uses a wrapper and a pinned FormosanBank commit. |
| **RauDong** | `remove_accents.py` strips acute accents from standard FORM after the fact; README says "we do not have a reproducible pipeline." Phonology profile unstated. |
| **Siraya_Gospels** | Bespoke `regenerate_standard_tier.py` (line-break hyphen removals); historical Gravius orthography, not Ortho113; no phonology. Should not be standardized. |
| **WakelinTexts** | Standard tier = original minus hyphens; conversion table `Yami_Wakelin_113.tsv` "should not be taken seriously"; orthography unidentified. |
| **YeddaPalemeqBlog** | Manual hand-correction of `/` and `()` alternates (AUDIO removed for ungrammatical sentences); README: "caution is suggested in reproducing this corpus." No `manual_edits.xml`. |

## Group 3 — No text (skip)

| Corpus | Note |
|---|---|
| TangRecordingsOfTaroko | Audio only; untranscribed. |
| Whitehorn_Collection | Audio only; XMLs are audio-pointer metadata. |

## Group 4 — Underspecified pipeline / unknown phonology profile → needs a call

| Corpus | Gap |
|---|---|
| MontgomeryTexts | README documents no standardize/add_phonology pipeline at all (Amis, thin README). |
| ILRDF_Dicts | `standardize` run with no TSV (u→o only); **no add_phonology documented** — unclear how existing PHON (if any) was made. 16 languages. |
| Paiwan_Stories | `standardize --copy`; phonology "the usual way", **no profile named**. |
| NTU_Paiwan_ASR | `standardize --copy`; add_phonology **profile not stated**; full reproduction needs private inputs (published XML is present though). |

## Recommendation

Proceed on **Group 1** now (safe, orthography known). For **Group 2** and **Group 4**,
get the maintainer's decision per corpus: skip, run the full documented pipeline
(where the post-std scripts live in `CodeAndDocs/`), or rerun std+phon and reapply
the available post-std steps. **Group 3** is out of scope. Note: for Group 2, a
std+phon-only rerun would make the audit diff dominated by the *loss* of
post-standardization edits, not by script improvements — and must not be committed.
