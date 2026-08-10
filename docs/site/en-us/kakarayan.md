---
icon: magnifying-glass
---

# Kakarayan

[Kakarayan](https://formosanbank.github.io/kakarayan/) is the public web interface for FormosanBank. It provides corpus search, language-learning tools, research downloads, and developer resources without requiring an account or a paid backend.

{% hint style="info" %}
**Open Kakarayan:** [formosanbank.github.io/kakarayan](https://formosanbank.github.io/kakarayan/)
{% endhint %}

## What can I do with it?

### Learners

* Look up words and morphemes in the dictionary view.
* Search for words and phrases in attested corpus sentences.
* Search from a Formosan language into an available translation language, or start with a translation and find the corresponding Formosan expressions.
* Save cited words and sentences to a private study deck in the browser.
* Review cards with a simple spaced-repetition schedule and export backups or Anki-compatible TSV.
* Record and replay pronunciation practice on the device.
* Use reviewed FormosanBank orthography conversion tables.

Dictionary and sentence results remain separate views on the same lookup page. Results identify the language, dialect, corpus, translation language, and source record. Where available, they also expose original and FormosanBank-standard forms, interlinear tiers, audio evidence, citations, and stable record links.

### Linguists and educators

* Filter by language, corpus, dialect, translation language, and available linguistic tiers.
* Inspect sentences, words, morphemes, translations, phonology, glosses, and audio references while retaining source provenance.
* Build a selected dataset and export CSV, TSV, JSON, JSON Lines, Parquet, plain text, interlinear text, or audio-reference data.
* Download a reproducible recipe recording the release, filters, fields, and ordering used for a browser export.
* Download prepared whole-release packages, including SQLite, tabular data, spreadsheets, CLDF, text exports, metadata and audio references, and time-aligned formats.

The browser dataset builder is intended for focused selections. Large prepared packages are stored with the corresponding [Kakarayan data release](https://github.com/FormosanBank/kakarayan/releases), rather than inside the GitHub Pages site.

### Developers

Kakarayan publishes a versioned static JSON API at:

```text
https://formosanbank.github.io/kakarayan/api/v1/
```

The API includes release metadata, languages, corpora, rights, model and orthography catalogues, downloads, and the search-shard manifest. JavaScript, Python, and R clients are maintained in the [Kakarayan repository](https://github.com/FormosanBank/kakarayan).

Start with `meta.json` and pin its release ID before reading other endpoints. The static API is the reliable public contract. An optional read-only live API may be available for convenient queries, but applications should not depend on it for essential access.

## Machine translation and speech recognition

Kakarayan can connect directly to public FormosanBank machine-translation and automatic-speech-recognition services. These tools are optional. The interface identifies the external service and asks before sending text or audio.

Model output is an unreviewed draft, not a correction, authoritative translation, pronunciation score, or community endorsement. Free public services may also sleep, take time to start, rate-limit requests, or be temporarily unavailable. Corpus lookup, downloads, and local study tools continue to work without them.

## How does it work without a backend?

Each public data release is built in advance from one exact commit of the public [FormosanBank repository](https://github.com/FormosanBank/FormosanBank). The build creates checksummed metadata, compact vocabulary indexes, and compressed search shards. When someone searches, the browser reads the relevant index, downloads only the candidate shards, and checks the matching records locally.

GitHub Pages serves the application and browser-search data. GitHub Releases holds the larger research packages. The application therefore does not need a database server to answer ordinary searches.

Study cards and review state remain in the browser's local storage unless the user exports them. Kakarayan has no user accounts, cloud study synchronization, or hidden learner analytics.

## Releases, sources, and responsible use

Every Kakarayan release records both the Kakarayan application commit and the exact FormosanBank source commit used to build its data. Search results and exports retain corpus, source, record, citation, and rights information. FormosanBank XML remains the canonical source.

Corpus records are attestations from named sources. They should not be treated as universal grammar rules, and corpus frequency should not be treated as a claim about correctness or speakers.

Using Kakarayan does not replace the source-specific terms attached to the data. Users must follow the [FormosanBank Terms of Use](additional-resources/terms-of-use.md), the [AI Use and Commercial Licensing policy](additional-resources/ai-use-and-commercial-licensing.md), and every applicable corpus or upstream-source notice. Academic and redistributed work must cite FormosanBank and the individual source corpora.

## Links

* [Open Kakarayan](https://formosanbank.github.io/kakarayan/)
* [Kakarayan source code and technical documentation](https://github.com/FormosanBank/kakarayan)
* [Versioned data releases and research downloads](https://github.com/FormosanBank/kakarayan/releases)
* [Report a public-site problem](https://github.com/FormosanBank/kakarayan/issues/new)
* [Browse the canonical FormosanBank repository](https://github.com/FormosanBank/FormosanBank)
