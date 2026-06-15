# PDF/XML Visual Spotcheck

This report compares cropped PDF page images against the final FormosanBank XML for high-risk examples raised during QC.

## Slash options: example 6a

- PDF page image crop: `data/processed/spotcheck_images/spotcheck_01_page_0028.png`
- Expected XML handling: Source `hiya/laqi` and segmentation are preserved in original sentence/word FORM; sentence standard FORM is de-segmented and the source Mandarin free translation with slash is retained for manual QC.

- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E006A1` page=28 ex=6a
  - FORM original: `M-kan qlupas ka hiya/laqi.`
  - FORM standard: `Mkan qlupas ka hiya/laqi.`
  - TRANSL zho: `他/小孩要吃桃子`

## Parentheses and Ch1 Ex11a

- PDF page image crop: `data/processed/spotcheck_images/spotcheck_02_page_0032.png`
- Expected XML handling: Ch1 Ex11a is included. Parenthetical source text is not a blanket rejection reason; standard forms conservatively remove parenthetical material.

- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E011A` page=32 ex=11a
  - FORM original: `Malu bi tunux ka isu.`
  - FORM standard: `Malu bi tunux ka isu.`
  - TRANSL zho: `你的頭腦很好。(你很聰明)`
- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E011E` page=32 ex=11e
  - FORM original: `N-tama ka patas gaga. (Patas tama ka gaga.)`
  - FORM standard: `Ntama ka patas gaga.`
  - TRANSL zho: `那本書是爸爸的。(那個是爸爸的書)`

## Page-break translation: example 26c source page

- PDF page image crop: `data/processed/spotcheck_images/spotcheck_03_page_0042.png`
- Expected XML handling: The Truku/gloss lines appear at the bottom of page 42 and the free translation continues at the top of page 43.

- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E026C` page=42 ex=26c
  - FORM original: `Wada p-riyax ka hidaw da.`
  - FORM standard: `Wada priyax ka hidaw da.`
  - TRANSL zho: `太陽已經下山了。`

## Page-break translation: example 26c continuation

- PDF page image crop: `data/processed/spotcheck_images/spotcheck_04_page_0043.png`
- Expected XML handling: The top-of-page Mandarin line is used as the source free translation for example 26c.

- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E026C` page=42 ex=26c
  - FORM original: `Wada p-riyax ka hidaw da.`
  - FORM standard: `Wada priyax ka hidaw da.`
  - TRANSL zho: `太陽已經下山了。`

## Parenthesized affix: Ch4 Ex4c

- PDF page image crop: `data/processed/spotcheck_images/spotcheck_05_page_0127.png`
- Expected XML handling: Original sentence and word FORM values keep source morphology/segmentation; sentence standard FORM removes parenthetical morphology conservatively.

- `HSU_LOWKING_TRUKU_WORDFORMATION_2008_C04_E004C` page=127 ex=4c
  - FORM original: `Ma (m)-klaway bi ka seejiq gaga.`
  - FORM standard: `Maklaway bi ka seejiq gaga.`
  - TRANSL zho: `為什麼那麼人跑步那麼快？`

## Result

- Spotcheck status: PASS
- No OCR was used for these comparisons; page images are audit renderings of the source PDF.
- Final XML remains under `Final_XML/Truku/`; screenshot crops and this report stay outside `Final_XML/`.
