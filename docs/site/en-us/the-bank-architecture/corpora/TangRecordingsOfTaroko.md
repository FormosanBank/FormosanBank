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
| Morphologically segmented | 0 |
| Glossed words | 0 |

***

<!-- CORPUS STATS END -->


## **Access Details**

* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/TangRecordingsOfTaroko).
* `CodeAndDocs/generate_xml.sh` rebuilds all 30 XML files from an extract of the Paradisec item metadata committed alongside it. The recordings themselves are not an input, so the corpus reproduces without downloading any audio.
* The published audio is pinned by identity: `CodeAndDocs/audio_manifest.json` records the byte size and SHA-256 of all 30 recordings against an immutable Hugging Face revision, and `CodeAndDocs/verify_sources.py` checks them — including `--live`, which compares against the hosted copy in one API call without downloading 13.6 GB. Nothing is resampled or converted; the files are the 44.1 kHz stereo originals as deposited.
* **Known deviation.** The *metadata* extract is not covered the way the audio is: it is the only Paradisec metadata FormosanBank holds, and nothing in the repository re-fetches it or checks it against the catalogue — there is no `refresh_source.sh`. This is accepted deliberately: AIT1 is a closed archival deposit, recorded in 1997 and published in 2016, so re-downloading an immutable record would add machinery without adding assurance. The reproduction guarantee is therefore that the published XML follows from the committed extract, not that the extract follows from Paradisec. The extract is upstream material rather than FormosanBank's own output fed back in: it enumerates 61 files where the corpus publishes 30, carries archival fields the XML has no place for, and has been unchanged since the corpus was first committed. The FormosanBank commit the published XML was built against is recorded in [`CodeAndDocs/provenance.json`](https://github.com/FormosanBank/FormosanBank/blob/main/Corpora/TangRecordingsOfTaroko/CodeAndDocs/provenance.json).

***

## **Copyright**

**License:** CC BY-NC 4.0

Prof. Apay Tang granted FormosanBank permission to publish these recordings on 4 May 2025. The value was written `CC BY-NC` until September 2026; an unversioned Creative Commons value means 4.0, so spelling out the version restates the same licence rather than changing it.

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

* Tang, Apay. (1997). Traditional Truku stories. Paradisec. https://dx.doi.org/10.4225/72/56EC22110B85A
