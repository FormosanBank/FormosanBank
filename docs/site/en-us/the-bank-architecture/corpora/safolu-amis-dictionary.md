# Safolu Amis Dictionary

The Safolu Amis Dictionary contains Amis examples from the dictionary compiled by Safolu Kacaw Lalanges / Tsai Chung-Han (蔡中涵), with Mandarin (Chinese) translations where the source supplies them. The current data is the generated `docs/s` JSON in the [g0v Amis Moedict](https://github.com/g0v/amis-moedict) project at commit `e7c6976a0766e9b0aeb7083e2c06db60f5485252`; the deprecated [miaoski/amis-safolu](https://github.com/miaoski/amis-safolu) generator at commit `f512d5ba0d08f81b26093a9b7b4a85acac760a30` records the pipeline provenance.

The source audit accounts for all 49,419 example fields. The canonical corpus contains 49,179 records after 261 duplicate source rows are ledgered and 22 unrecoverable fields are ledgered as rejected. It preserves 140 distinct additional Chinese readings as alternative translations and retains 269 Amis-only records for which the source gives no translation.

Each sentence carries source-faithful Safolu spelling in the `original` FORM tier, an Ortho113 `standard` FORM derived through the reviewed Coastal Amis conversion table, and separately generated original and standard PHON tiers. The source distinguishes `o` and `u` and contains both legacy `g` and current `ng` spellings for /ŋ/, so the standard tier is not simply a copy of the original. The corpus stops at the sentence level. It has no audio and no word or morpheme segmentation because the Moedict examples contain no source-attested aligned analysis.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>Coastal |
| --- | --- |
| Word count | 243,699 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 242,687 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Safolu-Amis-Dictionary).

***

## **Copyright**

CC BY-NC (per the frozen `miaoski/amis-safolu` README; the current data source is `g0v/amis-moedict` `docs/s`).

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

Tsai, Chung-Han (Safolu Kacaw Lalanges). (n.d.). *Amis dictionary*. Provided to the g0v Amis Moedict project. https://amis.moedict.tw/
