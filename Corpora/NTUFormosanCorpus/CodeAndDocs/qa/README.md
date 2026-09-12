# NTU corpus QA: regression checking

This directory answers one question: **did a change to the build make the corpus
better or worse, and where?**

It is not a validator. The repository's validators (`QC/validation/validate_xml.py`
and friends) decide whether the XML is *legal*. These tests measure how well the
XML holds together as a glossed corpus — whether the word tier accounts for the
sentence, whether every morpheme a form implies actually has an `M`, whether the
glosses sit in the right language slots. A file can be perfectly valid and still
score badly here.

## Why a baseline instead of a threshold

Almost none of these tests can honestly be expected to reach 100%. The source
has sentences nobody segmented, words nobody glossed, and translations that
belong to a longer span than the sentence they sit on. A fixed pass mark would
either be so low it caught nothing or so high it failed forever.

So the recorded score *is* the specification. `baseline.tsv` holds what each test
achieved on the corpus as published. Any rebuild is compared against it:

* a score that **drops** is a regression, and the run exits non-zero;
* a score that **rises** is reported, so the baseline can be moved deliberately;
* a test that appears or disappears is reported too, because a test that stops
  running is indistinguishable from a test that passes.

That last point matters more than it looks. Several tests here are scoped — they
only apply to sentences that have a word tier, say — so deleting the failing
material can make a score rise without anything improving. Reporting the
denominator changes is what keeps that visible.

## Usage

```bash
# score a rebuilt tree against the baseline
python check_regressions.py --subcorpus stories \
    --xml  ../../XML/Stories \
    --json ../story

# after a change whose effect you have examined and accepted
python check_regressions.py --subcorpus stories \
    --xml ../../XML/Stories --json ../story --update
```

`--subcorpus` is one of `grammar`, `sentences`, `stories`. Grammar uses a
different suite (`grammar_xml_tests.py`) because it carries a single Mandarin
gloss, while sentences and stories carry Mandarin *and* English
(`sentence_xml_tests.py`); a test that demands both glosses would be wrong for
grammar and a test that demands one would be too weak for the others.

`--update` never runs on its own. A baseline that moves by itself cannot catch
anything.

## Files

| file | what it is |
|---|---|
| `check_regressions.py` | the runner and comparator |
| `baseline.tsv` | the recorded score per subcorpus and test |
| `grammar_xml_tests.py` | the suite for the one-gloss Grammar subcorpus |
| `sentence_xml_tests.py` | the suite for the two-gloss Sentences and Stories |

## Reading a result

```
=== stories: 18 tests scored against baseline
  REGRESSED  15 S has a W tier                              99.9 ->     93.9
  improved   17 every implied morpheme has an M             92.8 ->     99.3
```

A pair like that is the normal shape of a real change: withdrawing an
unsupportable analysis costs one test and buys another. The tool's job is to
make the trade explicit rather than to pass judgement on it.
