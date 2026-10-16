# Source manifest

Verified 2026-08-21. Publication date corrected 2026-09-10 — see below.

| Field | Verified value |
|---|---|
| Work | B. Sato / 佐藤文一, “Native Songs from Taisha-sho, Pazeh Tribe, Formosa” / 大社庄の蕃歌 |
| Container | *Nanpo Dozoku: The Ethnographical Journal of the South-East Asia and Formosa*, vol. III, no. I |
| Publication date | April 1931 |
| Article pages | Printed pp. 116–126 |
| Publisher | Nanpō Dozoku Gakkai / 南方土俗學會, Taihoku |
| NTU article record | https://dl.lib.ntu.edu.tw/s/tj/item/812667 |
| NLPI bound-issue record | https://das.nlpi.edu.tw/handle/a678g |
| Basecamp source | Card 8538287698, attachment `png2pdf (3).pdf` |
| Local path | `Private/source/nanpo_dozoku_v3n1_taisha_songs_1931.pdf` |
| SHA-256 | `094658186d845c0fd1fae2da6a8c41870734742a08e86fcfa97815710e1f485e` |
| Size/type | 16,508,391 bytes; PDF 1.7; unencrypted; image-only |
| Extent | 14 PDF pages: printed pp. 116–126, colophon, English contents, and Japanese cover/contents |
| Rights/license | Not stated in the source. Published CC BY-NC 4.0 by project determination, 2026-09-10 — see Rights boundary below |
| Access | Source scan stays private; the corpus is cleared for publication under CC BY-NC 4.0 |

## Identity and completeness

The Basecamp attachment is the source used for extraction. It begins with the
section-I heading on printed p. 116, ends with the section-III free summary on
p. 126, and includes the issue's colophon and contents material. Its exact size
matches the Basecamp attachment metadata. All 14 pages were visually reviewed
and are represented in `intermediate/source_ledger.csv`.

The language is Pazeh, not Bunun. The English title identifies “Pazeh Tribe,”
and the song forms align with the Pazeh material represented by the source.
The XML therefore uses ISO 639-3 `pzh` and Glottocode `paze1234`.

## Date and pagination decision

**The issue is April 1931.** The cover of the bound issue reads
“Vol. III, No. I, April. 1931” and lists 大社庄の蕃歌 in its contents, so the
date is stated on the item itself, next to this very article. Maintainer,
2026-09-10, reading the attachment directly. The citation, the BibTeX entry,
the XML filenames and all 83 sentence identifiers use 1931 and agree.

An earlier pass of this manifest asserted April 1934, on the strength of two
claims: that the Japanese cover gives Shōwa 9, and that the NTU Library
catalog files 大社庄の蕃歌 under `南方土俗 19340400`. That conclusion is
withdrawn. The first claim contradicts what the cover actually reads and
should be treated as an error in the earlier pass rather than as evidence.

Two things remain genuinely unresolved, and are recorded here so the next
reader does not have to rediscover them:

- The NTU catalog record (item 812667) was reported as carrying a 1934 date.
  Nobody has re-checked it since the correction. If it does say 1934, then
  either the catalog is wrong about this issue or it describes a different
  printing; the item in hand is what the citation follows either way.
- *Nanpo Dozoku* began publication in 1931, so a third volume dated April 1931
  is unexpected on its face. The cover is nonetheless explicit, and an
  unexpected volume number is weaker evidence than a printed date.

Neither point is a reason to change the citation, and neither has been used to.

The article itself starts at printed p. 116 and ends at p. 126. Printed pp. 114
and 115 belong to the preceding article, so they are not part of this work.

The NLPI record at handle `a678g` catalogs four Volume 3 issues and explicitly
lists both Volume 3, No. 1 and “大社庄の蕃歌.” During this review, its live file
viewer served images labeled Volume 2, No. 4. The viewer images were therefore
not treated as the extraction source or as page-level evidence.

## Rights boundary

The attachment and the inspected catalog records contain no reuse licence, and
the Basecamp discussion leaves Sato's death date unresolved. Nothing in that
has changed; what changed is the decision taken in spite of it.

**The corpus is published under CC BY-NC 4.0** by project determination,
2026-09-10. This is not a grant from a rights holder — no heir has been
identified and no correspondence exists. The full statement is in the Rights
section of `../../README.md`, which is the canonical place for it (POL-044);
it sets out the unclear evidence about the author's date of death, the
transformative-use argument, the balance of community need against the
unlikely commercial interests of unknown heirs, and a contact route for anyone
claiming the copyright. It is not restated here, so there is one copy to keep
current.

`TEXT/@copyright` is `CC BY-NC 4.0`, exactly one of the values in
FormosanBank's `rights_vocabulary.csv` (POL-042). The PDF stays outside Git.
