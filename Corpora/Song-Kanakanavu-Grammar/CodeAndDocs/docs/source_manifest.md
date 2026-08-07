# Source manifest

- Basecamp card: https://3.basecamp.com/4067638/buckets/31258415/card_tables/cards/10081339846
- Citation: Song, Limei. 2018. *Kanakanafu yu yufa gailun* [Introduction to Kanakanavu Grammar]. *Taiwan nandao yuyan congshu*, 16. Council of Indigenous Peoples.
- Official reader: https://alilin.cip.gov.tw/ebook/5949734115b6abe6caf971/HTML5/pc.html#/page/1
- Official manifest: 268 page images, reader update timestamp `2018/07/30 17:29:49`
- Local image-source compilation: `raw_data/source.pdf`
- Local PDF SHA-256: `dcd553f0ab59d55570a27e859cf60b1df22c5ed873018a192d167a0312079893`
- Official positioned text reference: `raw_data/official_text.jsonl`
- Text reference SHA-256: `47fc6dc5a22e263b57d96781cb39c0d9dbd3fb77a6189609024be2801347d5ab`
- Local verification: 268 PDF pages and 268 JSONL page records; PDF size 29,034,677 bytes
- Acquisition method: `scripts/acquire_source.py` downloads every numbered official page image and its matching `iPhone/text/<page>.xml` record, verifies the declared page count, and compiles the images in order.
- Source authority: the official page images. The positioned text XML is a comparison aid and does not override visible page content.
- Dictionary source: language-sorted Appendix 2A on reader pp. 193-206, cross-checked against the duplicate Chinese-sorted Appendix 2B on pp. 207-220.
- Rights status: the author (Li-May Sung) granted permission — recorded in the Basecamp evidence attached to card `10081339846` — to publish this corpus under CC BY-NC 4.0 (Creative Commons Attribution–NonCommercial). The derived corpus is redistributable under those terms (attribution required, non-commercial use only); each `<TEXT>` element's `copyright` attribute records the license.
