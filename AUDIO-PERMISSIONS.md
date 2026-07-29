# Audio Publication Permissions

Hugging Face audio publication is approved source by source. A dataset may be
public only when `audio_permissions.json` records either:

1. a direct grant allowing FormosanBank to redistribute that source's audio; or
2. an upstream license that explicitly covers the source audio and permits
   redistribution.

A generated XML `copyright` value, an accessible audio URL, a dataset-card
license, or the general FormosanBank terms is not sufficient evidence. The
central terms do not replace source rights.

`audio_sources.json` is therefore an allowlist, not an inventory of everything
ever uploaded. The validator rejects any public download source whose
`permission_id` is absent, pending, lacks evidence, or does not name the exact
Hugging Face repository.

## Permission-verified public audio

| Source | Permission basis in this repository | Source license recorded here | Hugging Face |
| --- | --- | --- | --- |
| Apay Tang / PARADISEC Taroko recordings | [Direct inclusion permission](Corpora/TangRecordingsOfTaroko/README.md) and [source-specific XML provenance](Corpora/TangRecordingsOfTaroko/XML/Truku/AIT1-002-1.xml) | CC BY-NC, version not specified | Public |
| John Whitehorn / University of Cambridge collection | [Upstream collection record](Corpora/Whitehorn_Collection/README.md) and [item-specific audio provenance](Corpora/Whitehorn_Collection/XML/Paiwan/2_1144_side_a_whitehorn.xml) | CC BY-NC, version not specified | Public |
| Wilang Yutas recordings | [Direct republication permission](Corpora/WilangYutasVideos/readme.md) and [CC BY-NC permission note](Corpora/WilangYutasVideos/CodeAndDocs/scripts/make_xml.py) | CC BY-NC, version not specified | Public |

These three repositories contain 3,215 audio files. The 36 files declared in
`audio_extras.json` come from the same three permission scopes.

## Withheld pending source-specific permission

| Source | Why it is not public-downloadable | Current Hugging Face access |
| --- | --- | --- |
| ILRDF dictionaries | The [official copyright notice](https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116) requires permission outside its stated exceptions. The generated CC label is not independent evidence. | Private: aggregate plus 16 language repositories |
| NTU Formosan Corpus grammar | No written audio redistribution grant was located. | Private |
| NTU Formosan Corpus stories | No written audio redistribution grant was located. | Private |
| NTU Paiwan ASR | No written audio redistribution grant was located. | Private: two processed repositories and one raw repository |
| Paiwan Stories | No written audio redistribution grant was located. | Private |
| Yedda Palemeq | Its processing script generates the license label; no independent redistribution grant was located. | Private |
| ePark picture-book platform | The [official license](https://web.klokah.tw/creativeCommons/) contains exceptions for source-specific material, and the [official guide](https://web.klokah.tw/guide/) describes user recordings. Per-file coverage is unresolved. | Private |
| ePark nine-level materials | Official-license exceptions have not been resolved per audio source. | Private |
| ePark senior-high sentence patterns | Source files were supplied separately; no audio redistribution grant was located. | Private |
| ePark junior-high sentence patterns | Official-license exceptions have not been resolved per audio source. | Manual gate |
| ePark contextual materials | Official-license exceptions have not been resolved per audio source. | Manual gate |
| ePark daily conversation | Official-license exceptions have not been resolved per audio source. | Manual gate |
| ePark picture stories | Self-authored/source-specific exceptions have not been resolved per audio source. | Manual gate |
| ePark cultural materials | Self-authored/source-specific exceptions have not been resolved per audio source. | Manual gate |
| ePark vocabulary | Official-license exceptions have not been resolved per audio source. | Manual gate |
| ePark reading and writing | Self-authored/source-specific exceptions have not been resolved per audio source. | Manual gate |
| ePark essays | Self-authored/source-specific exceptions have not been resolved per audio source. | Manual gate |
| Raw ePark package | Mixed sources have not received a file-level permission review. | Private |

Manual-gated repositories require explicit owner approval before any file can be
downloaded. They remain gated only because the Hugging Face organization cannot
make more repositories private without exceeding its private-storage quota.

## Publication procedure

Before making any additional audio public:

1. Identify the exact source and rights holder for every audio file.
2. Add the written grant or upstream audio license to the source's
   `Corpora/<corpus>/README.md` or another stable source-specific record.
3. Add or update the source entry in `audio_permissions.json`.
4. Add the exact Hugging Face repository to `audio_sources.json`.
5. Run `python QC/validation/validate_hf_audio.py` anonymously.
6. Review the dataset card and publish only after the permission check passes.

If permission is unclear, the status remains `withheld_pending_permission`.
