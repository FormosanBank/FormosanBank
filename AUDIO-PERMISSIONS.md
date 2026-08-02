# Audio Publication Policy

FormosanBank uses the public repository as the publication boundary:

- If a corpus's XML is published under `Corpora/` in FormosanBank, its associated audio is public under the same license recorded in the XML.
- Publication permission is recorded on the corresponding Basecamp corpus card.
- Audio from a private development repository stays private and is not licensed for reuse.
- When a development corpus is published into FormosanBank, its audio access and license must be updated at the same time.

`audio_permissions.json` records this state for every FormosanBank Hugging Face audio repository. `audio_sources.json` lists the 21 canonical public datasets used by the download scripts. The 16 per-language ILRDF repositories are public compatibility mirrors, not additional canonical downloads.

## License versions

Use the latest version of the license named in the XML unless the publication permission comes from material already released under a specific Creative Commons version. In that case, retain the source's version.

## Published audio

| Published XML | Audio license | Hugging Face repositories |
| --- | --- | --- |
| ILRDF dictionaries | CC BY-NC 4.0 | Aggregate dataset plus 16 language mirrors |
| NTU Formosan Corpus grammar | CC BY-NC 4.0 | Grammar dataset |
| NTU Formosan Corpus stories | CC BY-NC 4.0 | Stories dataset |
| NTU Paiwan ASR | CC BY 4.0 | Two published audio datasets |
| Paiwan Stories | CC BY-NC 4.0 | One dataset; the three WAV files also remain in FormosanBank |
| Apay Tang / PARADISEC Taroko recordings | CC BY-NC 4.0 | One dataset |
| John Whitehorn / Cambridge recordings | CC BY-NC 4.0 | One dataset |
| Wilang Yutas recordings | CC BY-NC 4.0 | One dataset |
| Yedda Palemeq recordings | CC BY-NC 4.0 | One dataset |
| ePark published topics | CC BY-NC-SA 4.0 | Eleven topic datasets |

The canonical download contains 525,770 audio files. Files listed in `audio_extras.json` belong to the same published corpora and use the same licenses.

## Private development audio

These repositories remain private and are not licensed for reuse:

- `FormosanBank/NTU_Paiwan_Raw`
- `FormosanBank/ePark3_Raw`

Raw or working audio from any other private Formosan-X development repository follows the same rule.

## Publishing a development corpus

When a corpus moves from a private development repository into FormosanBank:

1. Confirm publication approval on its Basecamp card.
2. Add the final XML and its `copyright` license to `Corpora/<corpus>/`.
3. Change the associated Hugging Face audio from private to public.
4. Set the dataset-card license to match the XML, using the version rule above.
5. Add the repository to `audio_permissions.json` and, if canonical, `audio_sources.json`.
6. Run `python QC/validation/validate_hf_audio.py` anonymously.

CI checks that published repositories are public, development repositories are private, and every canonical dataset matches its XML audio contract.
