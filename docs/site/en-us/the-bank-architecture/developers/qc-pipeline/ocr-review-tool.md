---
icon: magnifying-glass
---

# OCR Review Tool

> Presents OCR-derived text one XML entry at a time and records human review findings in reusable CSV reports.

## What it's for

The OCR Review Tool is a desktop application under `QC/utilities/OCR Audit/`. It supports the human review stage for corpora created through optical character recognition. The tool does not decide whether text is correct and does not change the XML. Instead, it turns each reviewable XML line into a readable entry and makes common OCR problems quick to record.

Each entry shows:

* the original XML line number
* the text in plain-text form
* whether it is Formosan text, phonetic form, translation, or another entry type
* its phrase, word, or morpheme context
* `kindOf` and source notes when present

The reviewer can record missing, extra, or incorrect characters; missing, extra, skipped, or misformatted text; note-placement problems; and other errors. A finding can include a proposed correction.

{% hint style="warning" %}
The importer reads the XML line by line rather than parsing the document as an XML tree. Use it with FormosanBank's normally formatted XML, where a `FORM`, `PHON`, or `TRANSL` entry appears on one line. Reflowed or inline-heavy XML may not be presented correctly.
{% endhint %}

## Running it

Packaged Windows and macOS applications are included in the public repository:

* Windows: `QC/utilities/OCR Audit/dist/reviewOCR.exe`
* macOS: `QC/utilities/OCR Audit/macos dist/reviewOCR`

The Python source can also be run from the repository root:

```bash
cd "QC/utilities/OCR Audit"
python reviewOCR.py
```

The `data/` folder must remain in the same directory as the application or script being run. It stores the current session and report data. If you move a packaged executable, move its adjacent `data/` folder with it.

## Review workflow

1. Choose **Open New** and select an XML or text file.
2. Read the displayed entry and its type, tier, notes, and source line number.
3. Record any relevant error, or move to the next line when the entry is correct.
4. Use **Save** to preserve an in-progress session. The home screen can resume it later.
5. At the end of the file, or after choosing **End Review Early**, export the review.

If the reviewed source file moves, **Restore Lost Session** can associate the stored session with the file again.

## Output & side effects

The tool leaves the source XML unchanged. It maintains four files in its adjacent `data/` folder:

* `lastsession.json` records progress, the source path, and current findings.
* `allText.csv` stores the cleaned entries used by the active session.
* `errors.csv` records each reviewed XML line and its finding.
* `errorFreq.csv` counts repeated error-and-correction combinations so systematic OCR problems are easier to spot.

**Export Review** copies the two report CSVs to reviewer-selected locations. Review those reports before making reproducible corrections to the corpus XML.

## Related

* [QC Pipeline overview](README.md)
* [Manual edits](manual-edits.md)
* [sample_sentences.py](sample-sentences.md)
* [clean_xml.py](clean-xml.md)
