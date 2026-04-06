# SEALS 33

## **Overview**

These are the translated sections of the [2024 SEALS conference](https://sites.google.com/view/seals33/national-languages?authuser=0) (SEALS 33), graciously provided by the authors. 

The 2024 South East Asian Linguistic Society meeting took place in Taipei. The main page of the website were available in Seediq and Saisiyat, as well as Mandarin and English. 

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Seediq<br>NA | Saisiyat |
| --- | --- | --- |
| Word count | 543 | 585 |
| Total audio | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 | 0 |
| Translated words |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 136 | 177 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 402 | 434 |
| Morphologically segmented | 0 | 0 |
| Glossed words | 0 | 0 |

***

<!-- CORPUS STATS END -->


## **Corpus Processing**

1. **Process Raw Data to XML**:
   Run `process_raw.py` to process the raw data in the `raw_data` directory and structure it into XML format.

   ```bash
   python main.py
   ```

Currently, this only works for Eastern Paiwan.

**Output**
The processed XML files will be saved in `Final_XML/Paiwan`.

2. **Add dialect information**
Use `add_dialect.py` to add dialect information for the speakers.

```bash
python add_dialect.py --path Final_XML/Paiwan/speaker-name --dialect dialect
```

**Output**
- The XML roots will now have a `dialect` attribute. Since there are no glottocodes for Paiwan dialects, no glottocode attribute is created.

3. **Clean XML and standardize punctuation**

This isn't necessary because everything was already standardized. It is listed just to make it clear that we didn't forget to do it.

   ```bash
   python path/to/FormosanBankRepo/QC/cleaning/clean_xml.py --corpora_path Final_XML
   ```

**Outputs**
   - This will update the XML files.

**Notes**
   - This removes empty XML elements
   - It also standardizes orthography (more-or-less), though a lot of this was done in previous steps (not documented above)
   - Unicode is flattened so that diacritics are merged with the characters they modify
   - HTML escape codes are replaced with the corresponding characters

4. **Standardize orthography**

   ```bash
   python path/to/FormosanBankRepo/QC/utilities/standardize.py --corpora_path path/to/FormosanWikipedias/Final_XML --copy
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Creates a copy of every <FORM> element with kindOf="standard" attribute
   - Makes no changes, since the transcription is already the 113 Orthography.

5. **Add IPA**

   ```bash
   python ../FormosanBank/QC/utilities/add_phonology.py --corpora_path Final_XML --orthography Ortho113
   ```

**Outputs**
   - Updates XML files

**Notes**
   - Adds <PHON /> elements corresponding to each <FORM />, containing IPA.

***

## **Corpus Notes**

This section will be used to describe any notes regarding the corpus (e.g. explaining the presence of characters that aren't part of the standard orthography)

***

## **Access Details**

* The repo containing the SEALS 33 corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/SEALS33).

***

## **Copyright**

CC-BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* SEALS 33 Organizing Committee. (2024). 國家語言專區. SEALS 33. https://sites.google.com/view/seals33/national-languages