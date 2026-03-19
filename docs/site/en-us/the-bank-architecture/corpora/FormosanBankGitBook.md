# Presidential Apologies

## **Overview**

The FormosanBank GitBook provides documentation for FormosanBank. The long-term goal is to have translations, at least for the most critical pages, in each of the Formosan languages. 

Currently, we only have Paiwan (Eastern dialect).

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Paiwan<br>Eastern |
| --- | --- |
| Word count | 1,855 |
| Total audio | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 0 |
| Translated sentences |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 102 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 102 |
| Morphologically segmented | 0 |
| Proportion glossed | 0% |

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

* The repo containing the ePark corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/FormosanBankGitBook).

***

## **Copyright**

CC-BY-NC

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Ruan, X. (2025). Paiwan translation of FormosanBank manual.