---
icon: folder-open
---

# Folder structure

FormosanBank keeps each published corpus in its own directory under `Corpora/`. Initial corpus development happens in a separate development repository. Only the approved, reproducible output is ported into the public repository.

### Published Corpus Layout

The standard published layout is:

```text
Corpora/<CorpusName>/
├── README.md
├── XML/
├── CodeAndDocs/
└── download_audio_data.sh    # only when remotely hosted audio exists
```

* **`README.md`** describes the source, rights, known limitations, and how the published XML was produced.
* **`XML/`** contains the canonical public data.
* **`CodeAndDocs/`** contains the scripts and non-private source documentation needed to reproduce the XML.
* **`download_audio_data.sh`** downloads audio that is stored outside Git, normally from Hugging Face. It is included only when needed.

Older corpora do not always follow every part of this layout. New ports should follow it unless the source requires a documented exception.

Raw or private development material does not belong in the public corpus directory. Development repositories may contain a `Private/` directory, but nothing from it is ever ported into FormosanBank.

### Structure of the `XML` Directory

The `XML` directory may be grouped in the way that best preserves the source and keeps filenames manageable. Common layouts include:

1. **By language**

   ```text
   Corpora/ILRDF_Dicts/XML/Amis/Amis.xml
   Corpora/ILRDF_Dicts/XML/Paiwan/Paiwan.xml
   ```

2. **By subcorpus, then language**

   ```text
   Corpora/ePark/XML/ep1_九階教材/Amis/
   ```

3. **By language, then speaker**

   ```text
   Corpora/NTU_Paiwan_ASR/XML/Paiwan/Belmira/
   ```

4. **By ISO 639-3 code**

   ```text
   Corpora/Glosbe/XML/ami/
   Corpora/Glosbe/XML/tay/
   ```

A language-named directory is common, but it is not a schema requirement. QC and statistics tools recursively walk `XML/`, so the important requirements are valid XML, stable paths, and a layout that can be reproduced from `CodeAndDocs/`.

### Audio Layout

Audio files are usually gitignored and downloaded into `Corpora/<CorpusName>/Audio/`. A few small legacy corpora keep audio directly in Git.

The XML records the filename or document-level audio reference. Download scripts should reconstruct a layout that the audio resolver can match. Mirroring the relative XML organization is the clearest option, but the current tools also support common layouts such as dropping the leading language directory or locating a unique filename recursively.

For segmented audio, an XML sentence, word, or morpheme references a separate clip:

```text
XML/Amis/example.xml
Audio/Amis/example/example_S1.wav
```

For an unsegmented recording, `TEXT/@audio` identifies the document-level file and child AUDIO elements provide start and end offsets.

Do not assume that XML or audio basenames are globally unique. Keep the corpus directory structure intact unless you also update and validate every reference.

### Related Workflows

* [Porting a Corpus In](porting-a-corpus.md) describes how a finished development repository becomes this published layout.
* [FormosanBank XML Format](../formosanbank-xml-format.md) defines the file structure inside `XML/`.
* [Hugging Face](huggingface.md) explains the audio download scripts.
* [QC Pipeline](qc-pipeline/README.md) documents the recursive validators and statistics tools.
