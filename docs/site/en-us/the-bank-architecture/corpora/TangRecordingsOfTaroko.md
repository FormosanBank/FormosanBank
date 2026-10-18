# Tang Recordings of Taroko

These audio files were collected by Prof. Apay Tang, a member of the Truku tribe and a prominent preservationist and revitalizationist in the community. While permanently archived at Paradisec, Prof. Tang graciously agreed to include the audio in FormosanBank.

None of the audio are transcribed. There is slightly more meta-data at Paradisec, but not much.

***

<!-- CORPUS STATS START -->
## Corpus Statistics

| | Truku |
| --- | --- |
| Word count | 0 |
| Total audio | 21.4h |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transcribed | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Untranscribed | 21.4h |
| Translated words |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;English | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Mandarin | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Japanese | 0 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Dutch | 0 |
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## Notes and Issues

The committed metadata extracts are not independently checked against Paradisec. Joshua accepted this limit for the closed AIT1 deposit, recorded in 1997 and published in 2016, in [FormosanBank #197](https://github.com/FormosanBank/FormosanBank/pull/197). The extracts enumerate 61 source files and archival fields absent from our XML, and have been unchanged since the corpus's first commit. The 30 matching MP3s are treated as delivery copies of the WAV masters; the remaining file, `AIT1-001-2df.pdf`, has not been inspected or included.

Remote audio verification compares paths, sizes and hosted SHA-256 object IDs. It does not listen to the recordings or independently verify Paradisec. The verifier covers this 30-WAV inventory; it is not a general audit tool for larger datasets. If local hashes differ, move those copies aside before downloading and checking again.

## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/TangRecordingsOfTaroko).
* The published audio is pinned by identity: `CodeAndDocs/audio_manifest.json` records the byte size and SHA-256 of all 30 recordings against an immutable Hugging Face revision. `CodeAndDocs/verify_sources.py --live` checks the hosted identities without downloading 13.6 GB; `--local` hashes downloaded files. The downloader preserves the original 44.1 kHz stereo WAVs and verifies their bytes. It does not resample or upload audio.

## Corpus Processing

From a FormosanBank checkout, run:

```bash
Corpora/TangRecordingsOfTaroko/CodeAndDocs/generate_xml.sh
```

This rebuilds all 30 XML files from the four committed metadata extracts without downloading audio. The build's FormosanBank commit is recorded in [`CodeAndDocs/provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/TangRecordingsOfTaroko/CodeAndDocs/provenance.json); it does not select an older checkout. A Git-free export retains that record.

**POL-047 deviation:** These untranscribed recordings have no text tiers or manual edits, so only source-to-XML generation applies. Audio verification runs separately from the build.

***

## **Copyright**

**License:** CC BY-NC 4.0

Prof. Apay Tang granted FormosanBank permission to publish these recordings on 4 May 2025. The value was written `CC BY-NC` until September 2026; an unversioned Creative Commons value means 4.0, so spelling out the version restates the same licence rather than changing it.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A
