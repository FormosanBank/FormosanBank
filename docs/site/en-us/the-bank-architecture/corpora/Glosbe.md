# Presidential Apologies

## **Overview**

This corpus comes from the crowdsourced online dictionary Glosbe. Currently we have only included Amis, which was (at time of checking) the only reasonably sized dictionary. 

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Amis<br>UK |
| --- | --- |
| Word count | 91,201 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 91,201 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

The process involves several steps to extract, scrape, clean and format the data:

1. **Extract Common Words**:
```bash
python work/scripts/extract_words.py
```

**Output**: Generates list of most frequent Amis words from reference corpus

2. **Scrape Translations**:
```bash
python work/scripts/scrape_zh.py
```

**Output**: Raw translation pairs saved to JSON

3. **Deduplicate Translations**:
```bash
python work/scripts/dedupe_zh.py
```

**Output**: Cleaned JSON file with unique translation pairs

4. **Convert to XML Format**:
```bash
python work/scripts/make_xml.py
```

**Output**: FormosanBank XML format in `Final_XML/amis_glosbe.xml`

5. **Validate XML** (Optional):
```bash
python work/scripts/validate.py
```

**Output**: Validation report of XML structure

6. **Clean XML** (Optional):
```bash
   python work/scripts/clean_xml.py
```

**Output**: Standardized punctuation and cleaned XML

7. **Update XML**

Replace-all: <FORM> -> <FORM kindOf="original">

8. **Add Traditional Chinese**

This was done semi-automatically. It's not easily reproducible.

9. **Standardize**

It looks like it's Ortho94 (mostly). But conversion won't change anything relevant.

```bash
   python ../FormosanBank/QC/utilities/standardize.py --corpora_path Final_XML --copy
```

9. **Remove some colons**

Colons are used for introducing quotes in this text. However, colons have a specific meaning in the standard orthography, so replace with commas. 

```bash
   python work/scripts/fix_colon_quote.py
```

10. **Add IPA**

The IPA for Ortho94 is different from Ortho113, so go ahead and use it for the "original" tier.

```bash
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho94
```

***

## **Corpus Notes**

Because this is a crowd-sourced dictionary, its accuracy is uncertain.

***

## **Access Details**

* The repo containing the Glosbe corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/Glosbe).

***

## **Copyright**

CC-BY-SA

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Glosbe. (n.d.). Glosbe dictionary. https://glosbe.com. Accessed 2025.