# Orthography evidence

The Safolu source distinguishes `o` and `u` and mixes legacy `g` with current
`ng` for /ŋ/. The original FORM and PHON tiers preserve those source choices.

Primary evidence:

- Safolu K. Raranges (Tsai Chung-Han), 2013, “’Amis Writing System: A Dispute
  About ‘O’ And ‘U’,” *Aboriginal Language Forum* 49, pp. 72–73:
  https://d17u3w3ts5ihmp.cloudfront.net/storage/app/public/files/2663.pdf
- SHA-256 of the inspected two-page PDF:
  `f00a51ac472d5d8c3ba4b8877d1fe668ec79259af5f59aa1354c25ea83a62aae`.
- Li, Tai-yuan, 2013, *The Literation of Taiwanese Aboriginal Languages*,
  p. 27, footnote 55:
  https://www.ntl.edu.tw/public/ntl/4216/%E6%9D%8E%E5%8F%B0%E5%85%83%E5%85%A8%E6%96%87.pdf
- SHA-256 of the inspected 339-page thesis PDF:
  `f9a483664bc399f47173b3a8539439abeef801693b355c1857e757e0b03199da`.

The author describes rejecting a proposed blanket `u`-to-`o` replacement
because it would lose pronunciation and usage distinctions. Li documents that
older church writing commonly used `g` for Amis /ŋ/, while later writing mostly
uses `ng`. The pinned dictionary JSON provides direct internal confirmation:
95 records contain single `g`, modern `ng` is otherwise common, and converting
`g` to `ng` makes source rows S17561 (`tangila`) and S36898 (`tagila`) exact
standard-tier duplicates.

The deterministic derivation is therefore:

- original FORM: pinned source spelling;
- original PHON: `Orthographies/Safolu/Amis.tsv`, Coastal column;
- standard FORM: `Orthographies/ConversionTables/Amis_Safolu_113.tsv`, Coastal
  column, applied with `standardize.py --single-pass`;
- standard PHON: current `Orthographies/Ortho113/Amis.tsv`, Coastal column.
