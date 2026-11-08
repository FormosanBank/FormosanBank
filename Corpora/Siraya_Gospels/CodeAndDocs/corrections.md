# Recorded source corrections

The pristine POL-035 baseline is the 49 XML files from FormosanBank commit `52524b1f898ac5d919f23d9abd4852b36f8f9d31`, recorded in source_manifest.json. It includes earlier hand corrections and both rare combining-diaeresis examples. It is never regenerated from the retired OCR notebooks.

`manual_edits.xml` records 77 complete S edits on the shared stripped basis. Apply it only to fresh generated output. Keep records even when a later upstream fix makes one a no-op (POL-030).

| Records | Change | Evidence |
| --- | --- | --- |
| John 13:16 and 13:18 | Move the misplaced Dutch reading to verse 18, without rewriting it. | Joshua's [June 8 correction](https://github.com/FormosanBank/FormosanBank/commit/2662efd74b588eab55004b5848cad5224378e5d1); John PDF 98. |
| Matthew 14:1 | Remove the OCR plus sign after `tijdt`. | The same June 8 correction. |
| Matthew 17:2-27 | Remove 26 wrong-chapter Dutch copies. Their real occurrences remain at Matthew 18:2-27, including its three previously corrected spacing/hyphen cases. | The same June 8 correction; Matthew PDF 107-111. |
| Matthew 17:27 | Remove the following chapter heading from FORM and the appended beginning of Dutch 18:1. The actual 18:1 record remains. | Matthew PDF 107 places both below the chapter divider, outside verse 17:27. Original removed heading: `Ka sasat kytti-an'æb ki kæuighpa kilbægh ki soulat.` The complete old content remains in the baseline. |
| Matthew 18:28 | Restore `tpæpænæh` and `sât`, preserving the rest of the original tier. | Matthew PDF 111, bottom, and 112, top. |

Further scan review repairs only the recorded substrings, not whole-verse OCR replacements:

| Records | Repair | PDF page |
| --- | --- | --- |
| John 5:18, 5:23, 11:18, 18:23; Matthew 8:4 | Replace five spurious equals signs with the printed letters or hyphen; restore `Ti-ma-mang` and `gmail-lâ` on the same lines. | John 33, 34, 81, 125; Matthew 47. |
| John 5:28, 6:20, 6:27, 7:3 | Restore printed `Ynnâ`/`ynnâ` and `tæ'iä-papara`, where OCR produced digits. | John 35, 41, 42, 49. |
| John 5:42, 12:12 | Restore the opening parenthesis before `kamou` and the J in `Jerusalem`. | John 37, 89. |
| Matthew 16:10, 22:2, 23:14, 24:2, 24:19, 26:71, 27:53 | Restore missing closing brackets as parentheses, retaining the published bracket convention and all enclosed words. | Matthew 99, 132, 140, 145, 148, 171, 180. |
| Final verses of Matthew 2–10 and 12–27 | Remove 25 following-chapter headings outside the printed verse/divider; recover the clipped `la.` in 15:39 `Magda-la.`. All narrative verses and their IDs remain. | Matthew 21, 24, 28, 36, 41, 46, 51, 57, 64, 77, 86–87, 91–92, 97, 102, 107, 113, 118, 124, 132, 138, 145, 153, 160, 172, 182–183. |

The final original-symbol sweep also removes the duplicated verse label in Matthew 26:11 (PDF 162) and restores John 5:11 `ææ̈pag` (PDF 32), 8:44 `äou-si` (PDF 63), and 20:7 `lbæh` (PDF 137). The first preserves the printed combining diaeresis, not an ASCII approximation.

John 7:39 loses one spurious middle dot before `atta` (John PDF 55); the source's two opening periods and parenthesis remain.

John 12:28 and 12:33 retain unbalanced punctuation visible in the scan (John PDF 92). Source editorial brackets are not instructions to generate optional-word variants. The baseline retains every removed heading and the complete predecessor verses.

The June 8 Dutch edits were accidentally undone by the June 28 bulk refresh. Their restoration follows POL-050; it is not general deduplication of a narrative.

Reference translations are parsed from the retained editions, not hand rewritten. The parser preserves all verse continuations, including four nonempty `p` paragraphs that the previous importer missed, and the John 1:38/39 source partition. CUV `s1` headings are outside verse text; `r` references belong to the following section and are notes at its first verse; `f` editorial readings are translation notes. The complete USFM preserves that apparatus and its source placement.

Shared cleaning owns typography. Shared standardization first creates the copied tier. Joshua's [August 3 standard-tier correction](https://github.com/FormosanBank/FormosanBank/commit/de37a628c1df54787ec7ab5ad1567a73e6fad530) then applies only the retained CSV merges. Do not re-derive that list from changed word frequencies or strip other hyphens.
