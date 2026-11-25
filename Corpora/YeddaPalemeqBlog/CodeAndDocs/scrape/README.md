# Scrape code (not part of the reproduction path)

These are the scripts that produced the corpus from the live blog. **The
published build does not run them.** `CodeAndDocs/scripts/rebuild_xml.sh`
rebuilds the XML from the frozen snapshot in `../data/source_snapshot/`, with
no network access, and that is what `reproduce.sh` verifies.

They are kept here so the scrape itself stays inspectable and repeatable: this
is the code that decided what counts as a sentence, which words get a `W`, and
which parts of a post to ignore.

| Script | What it does |
| --- | --- |
| `download_html.py` | Walks the Blogger feed and caches every post's HTML locally |
| `analyze_blog_structure.py` | Parses the cached HTML into FormosanBank XML — sentence segmentation, the W tier, gloss matching, and the per-post exception lists |
| `download_audio.py` | Resolves the YouTube embeds referenced by each post and writes `AUDIO` elements |

`download_html.py` and `analyze_blog_structure.py` need `beautifulsoup4` (in the
repo `requirements.txt`). `download_audio.py` installs `yt-dlp` on demand.

To scrape, download the HTML into a gitignored folder, then parse it:

```
python3 scrape/download_html.py --output-dir Private/html_cache
python3 scrape/analyze_blog_structure.py --html-dir Private/html_cache --generate-xml
```

`--generate-xml` writes `XML/Paiwan_Yedda_Blog.xml` and two logs into the
current folder, so run it from a scratch folder (with an absolute
`--html-dir`) when comparing against the frozen snapshot.

## Gloss and translation text keeps the blog's spaces

Text that goes into the corpus is read with `visible_text()`: the text a reader
sees, with whitespace runs collapsed to one space. Until 2026-11-25 the scraper
used BeautifulSoup's `get_text(strip=True)`, which trims each text fragment and
joins the fragments with nothing, so every space next to an italic word was
lost (`the root is <i>kan </i>'eat'` → `the root iskan'eat'`). The frozen
snapshot was made by that version. `tests/test_scrape_text.py` checks the
extraction on three real posts saved under `tests/fixtures/blog_posts/`.

The rules that were written against the glued text (the `a;LIG` repair, the five
"X or Y" headword rules such as `taortua`, the `tja-(k)/'(a)ma` headword) now
compare with whitespace removed, so they fire on the same glosses as before.
The other "X or Y" headwords (`kama or ama`, `nua or na`, …) still match no word,
as before. Text used only to *locate* blocks in a post (the yellow-text ignore
list, next-block search keys) still uses `get_text(strip=True)`, unchanged.

## Re-scraping does not reproduce the snapshot

A fresh scrape is a *new* observation of a blog that is still live and still
editable. It will not be byte-identical to
`../data/source_snapshot/Paiwan_Yedda_Blog.xml`, and it is not meant to be:

- the frozen snapshot was taken by an earlier run of this lineage, and
  `analyze_blog_structure.py` has been edited since;
- the 2026-08-23 live-source audit found 24 sentence translations and 41 word
  glosses that the frozen scrape had truncated or missed. Those are applied by
  `scripts/build_xml.py` from reviewed tables, not by re-scraping;
- posts can change or disappear upstream.

So: use these scripts to re-derive the corpus from the blog as it stands today,
as a deliberate new pass that gets its own review. Use `rebuild_xml.sh` to
reproduce the published corpus.

## Per-post exception lists

`analyze_blog_structure.py` carries hand-maintained exception lists keyed by
post slug — `YELLOW_TEXT_IGNORE_LIST` and its siblings — recording places where
the blog's own formatting misleads the parser (a grammatical marker styled like
a headword, a gloss fragment styled like a sentence). Each entry is a judgement
about one post. A re-scrape inherits them; a scrape of new posts will need new
ones.
