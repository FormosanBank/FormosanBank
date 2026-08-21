---
icon: magnifying-glass
---

# Kakarayan

[Kakarayan](https://formosanbank.github.io/kakarayan/) is FormosanBank's public interface for corpus lookup, language learning, research data, and developer access. It requires no account.

{% hint style="info" %}
**Open Kakarayan:** [formosanbank.github.io/kakarayan](https://formosanbank.github.io/kakarayan/)
{% endhint %}

## Lookup

Dictionary and sentence search share one interface. A search can start with a Formosan expression or with a translation. Results can be narrowed by language, corpus, dialect, translation language, match type, and available evidence.

Dictionary results provide meanings, variants, corpus coverage, citations, and attested examples. Sentence results provide the source and FormosanBank-standard forms, translations, tokens, audio references, and interlinear or phonological tiers when the source contains them. Full records load only when opened.

## Learning tools

Learners can:

* save cited dictionary entries and sentences to a browser-local study deck;
* review cards and export a backup or Anki-compatible TSV;
* record and replay pronunciation practice;
* submit selected text or audio to named FormosanBank machine-translation or speech-recognition services;
* use reviewed orthography conversion tables; and
* keep local language notes.

Decks and review state stay in the current browser. Recordings remain in the active tab unless the user downloads one or explicitly submits it to the named speech-recognition provider. Kakarayan has no learner accounts or cloud synchronization.

Machine translation and speech recognition are optional Hugging Face services. A sleeping service may take time to start, and model output is an unreviewed draft rather than an authoritative translation or correction. Corpus lookup does not depend on model availability.

## Research and downloads

The research builder provides a small preview and a finite CSV, TSV, or JSON Lines export. A selection can include one Formosan language, optional corpus and dialect filters, Formosan or translation matching, evidence requirements, and explicitly chosen fields. Sentence, word, and morpheme translations retain their own tier owners.

Interactive exports are limited to 1,000 rows and 5 MiB. For complete or large-scale analysis, use a prepared artifact from the [Kakarayan data releases](https://github.com/FormosanBank/kakarayan/releases). The Downloads page records each artifact's scope, size, SHA-256 checksum, citation, rights, and included linguistic tiers. Canonical XML remains in the public [FormosanBank repository](https://github.com/FormosanBank/FormosanBank).

## Public API

Kakarayan has a required public, read-only query API. It supports dictionary and sentence search, record detail, frequency and summary queries, dataset previews, and finite exports. Every corpus route is pinned to an immutable release ID.

* [Interactive API reference](https://54-199-96-129.sslip.io/docs)
* [OpenAPI document](https://54-199-96-129.sslip.io/openapi.json)
* [Browser playground](https://formosanbank.github.io/kakarayan/#/developers)
* [Static release metadata](https://formosanbank.github.io/kakarayan/api/v1/meta.json)

The API accepts bounded `GET` requests only. It has no account, upload, write, or arbitrary SQL route. Applications should read the current release from `meta.json`, confirm that `/readyz` reports the same release, and retain that release ID in reproducible work.

## How it is hosted

Kakarayan separates the small interface from the large corpus read model:

```text
Browser
  -> GitHub Pages: interface and small release catalogues
  -> Tokyo query service: bounded read-only API requests
       -> local indexed SQLite database
  -> GitHub Releases: prepared research downloads
  -> Hugging Face: optional MT or ASR requests after consent
```

A publication build reads one exact commit of the public FormosanBank XML and creates an indexed SQLite read model, small catalogues, checksums, and prepared downloads. The 4 to 5 GB database is activated on the query server before traffic reaches it. Ordinary browsers never download the database or a corpus-wide search index.

At lookup time, the API normalizes the query and uses prebuilt SQLite indexes to retrieve a small result page. It does not parse XML or rebuild data during the request. This makes search practical on phones and slower connections while keeping the service simple enough for a small research group to maintain.

## Releases, citation, and rights

Every Kakarayan data release records the exact FormosanBank source commit and Kakarayan publisher commit. Search results and exports retain stable identifiers, corpus scope, source paths, citations, and rights references. FormosanBank XML remains canonical.

Corpus records are attestations from named sources. They are not universal grammar rules, and frequency is not a claim about correctness or speaker preference.

Using Kakarayan does not replace source-specific terms. Follow the [FormosanBank Terms of Use](additional-resources/terms-of-use.md), the [AI Use and Commercial Licensing policy](additional-resources/ai-use-and-commercial-licensing.md), and every corpus or upstream-source notice. Academic and redistributed work must cite FormosanBank and the relevant source corpora.

## Project links

* [Open Kakarayan](https://formosanbank.github.io/kakarayan/)
* [Kakarayan repository and technical documentation](https://github.com/FormosanBank/kakarayan)
* [Data releases and prepared downloads](https://github.com/FormosanBank/kakarayan/releases)
* [Report a public-site problem](https://github.com/FormosanBank/kakarayan/issues/new)
