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

`download_html.py` and `analyze_blog_structure.py` need `beautifulsoup4`, which
is **not** in the repo `requirements.txt` because nothing in the reproduction
path imports it. `download_audio.py` installs `yt-dlp` on demand.

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
