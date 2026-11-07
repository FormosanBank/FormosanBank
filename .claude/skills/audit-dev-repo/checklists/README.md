# Per-shape checklists for audit-dev-repo

Loaded after Step 0b (profile the corpus). Every corpus gets `every-corpus.md`;
the others apply when the profile says so, and a corpus usually matches more
than one (ePark is parallel, audio and word-glossed; NTU is glossed text and
audio; Song is grammar examples plus a dictionary appendix).

| Profile says | Load |
|---|---|
| any corpus | `every-corpus.md` |
| source is a dictionary, wordlist or lexicon (headwords, senses, example sentences under entries) | `dictionary.md` |
| W or M elements present, or the source prints interlinear glosses | `glossed.md` |
| S with TRANSL and no W/M (narratives, scripture, blogs, parallel sentences, grammar examples without glossing) | `text-with-translation.md` |
| AUDIO elements, or a download_audio_data.sh, or recordings in the source | `audio.md` |
| `Corpora/<Name>/` already exists on main (a re-port) | `re-port.md` |

Each item has the same four parts: **what to look for · how to check · what
counts as acceptable · an example from the bank**. The policy rule for the
third part, in the maintainer's words (2026-10-17): *"For 'what counts as
acceptable' policies that do not have tests are guidelines. The agent
shouldn't make decisions based on them that aren't run by the user for
approval. Where there are tests, HARD errors are HARD. SOFT warnings should be
raised to the user, with a description, categorization of different sources of
the SOFT warnings, etc."* So: a HARD validator finding is a defect; a SOFT
finding is raised to the maintainer with what it is and where it comes from;
a policy with no test is a guideline, and a departure from it is a question
for the maintainer, never a decision the audit makes alone.
