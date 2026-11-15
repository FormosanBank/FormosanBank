# Brief: where was each corpus's data collected? (READ-ONLY research)

## The maintainer's request, verbatim (2026-11-07)

> "I just added a new doc "110年原度原住民族語言能力認證測驗輔導班方言別" to QC/reference. It lists where
> various dialects are currently spoken. I'd like you to go through every corpus for which we have a dialect
> specified OTHER than ePark and Presidential Apologies. Check whether the corpus doc says where the data was
> collected. If so, compare against this list. If not, see if you can the PDF (you may need to look at the dev
> repo to get the PDF). Add that information to the corpus documentation if you find it. Then compare against
> the new list.
>
> I don't want anything changed now. I just want to know what matches and what doesn't. And what we don't know
> because we can't find the info."

Your part: **find and quote** where each assigned corpus's data was collected (or where its speakers / consultants /
storytellers / authors are from). You do NOT compare against the list and you do NOT write documentation: the
coordinating session does the comparison. "Add that information to the corpus documentation" is overridden by "I
don't want anything changed now".

## Hard rules

1. **Change nothing anywhere.** Do not edit, create, move or delete any file in any repo. The ONLY file you may
   write is your own output file named in your task. No `git` commands that write (no checkout, add, commit, stash,
   worktree). Careful with shell: in awk, `print x > y` writes a file; never redirect output into a repo.
   Any deviation from these instructions: stop and report it; don't implement it.
2. **Read FormosanBank files only from the worktree at current `main`:**
   `/tmp/claude-1000/-workspace-FormosanBank/e78edf4a-c5b9-400e-864e-ff685648c37f/scratchpad/fb-main`
   Do NOT read `/workspace/FormosanBank` (a shared checkout on another branch). Dev repos are siblings:
   `/workspace/Formosan-<Name>/` (use absolute paths; `git -C <abs path>` for git reads).
3. **Evidence only from this corpus's own sources.** Never infer one corpus's location from another corpus, from
   another language, or from general knowledge ("Xiuguluan is spoken in 光復, so probably 光復" is NOT evidence).
   If you know something from general knowledge, you may mention it once, labelled "GENERAL KNOWLEDGE, NOT FROM
   THE SOURCE", and it must not appear in the evidence fields.
4. **Quote verbatim**, in the source's own language and script (Chinese stays Chinese, romanized village names stay
   as printed). Give exact locations: file absolute path + line, or PDF page as BOTH the printed page number and
   the PDF page index; for JSON give the key path. Render scanned pages to images and look at them when there is no
   text layer (the Read tool reads PDFs with a `pages` parameter; pdfplumber and pypdfium2 are in
   `/workspace/FormosanBank/.venv` — you may run that Python, just don't write into a repo).
5. **Distinguish observed vs inferred.** "The book says consultants are from 互助村" = observed. "The storyteller's
   name suggests…" = inferred: label it.
6. **Say what the location applies to**: the whole corpus, specific texts/files, specific speakers. If a corpus has
   several speakers from different places, list each with which files are theirs (or counts, if many).
7. `xml:lang="trv"` means Seediq-or-Truku: `trv` + `dialect="Truku"` is Truku; any other trv is Seediq.
8. Network: the container reaches only GitHub and PyPI. Web sources (ILRDF, Glosbe, YouTube, Paradisec, blogs) can't
   be fetched; use only committed/local copies and say when the information would only exist online.
9. Also check each corpus's XML `<TEXT>` attributes (`citation`, `source`, `BibTeX_citation`) and any notes: some
   corpora record the village or storyteller there.

## What to look for

Any statement of where the material was recorded/collected, where the speakers/consultants/informants/authors/
storytellers live or come from: county 縣/市, township 鄉/鎮/市/區, village 村/里, community 部落/社, or romanized
names (e.g. "Iranmilek", "Hsinshe", "Wutai village"). Typical places: introduction / preface / acknowledgements /
"consultants" / "data" / "methodology" section of a book, thesis or paper; per-text headers in a text collection;
metadata JSON/TSV; video titles/descriptions.

## Output

Write full per-corpus detail to your output file (Markdown) using exactly this template per corpus:

```
### <Corpus folder name>
- Dialect label(s) in XML (xml:lang + dialect, with file counts): ...
- README statement about place (verbatim + line), or "README: none":
- Sources searched (absolute paths / what was searched: e.g. "text layer grep for 村|鄉|部落|village|consultant; read pp. i–xii, 1–20 as images"):
- LOCATION EVIDENCE (one bullet per quote):
  - "<verbatim quote>" — <where: abs path, printed p. X / PDF p. Y | line N | JSON key>
    applies to: <whole corpus | which files/texts/speakers>
    places named (as printed): <county / township / village / 部落>
- Observed vs inferred notes:
- Could not find / not knowable locally: <what is missing, and where it would be (e.g. only on a website)>
- Proposed README addition (text the maintainer could add later; do NOT add it): "<one or two sentences, citing the page>"
```

Then reply with a SHORT final message (under 600 words total): one line per corpus —
`<Corpus>: FOUND <places> (<source, page>) | NOT FOUND (<why>)` — plus the output file path. Put all detail in the
file, not in the reply.
