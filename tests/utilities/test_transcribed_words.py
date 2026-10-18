"""transcribed_words: words of sentences that have audio (on the S or on any of its W).

Defined 2026-10-18 for the documentation site's growth figures (the line
"total words transcribed"). On main at cbcaf0214 this differs from counting
S-level audio only by 98 of 2,637,835 words, all in ePark.
"""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "QC"))
import corpus_counts  # noqa: E402

XML = """<TEXT id="t" xml:lang="ami" dialect="Coastal">
  <S id="s1"><FORM kindOf="original">one two three</FORM><AUDIO file="a.wav" start="0" end="1"/></S>
  <S id="s2"><FORM kindOf="original">four five</FORM>
    <W id="s2w1"><FORM kindOf="original">four</FORM><AUDIO file="w.wav"/></W></S>
  <S id="s3"><FORM kindOf="original">six seven eight nine</FORM><AUDIO start="0" end="1"/></S>
  <S id="s4"><FORM kindOf="original">ten eleven twelve thirteen fourteen</FORM></S>
</TEXT>"""


def test_transcribed_words_counts_sentence_and_word_audio_with_a_file():
    record = corpus_counts.analyze_root(ET.fromstring(XML))
    # s1 (S audio, 3 words) + s2 (W audio only, 2 words); s3's AUDIO has no
    # file, s4 has none.
    assert record["transcribed_words"] == 5
    assert record["word_count"] == 14


def test_transcribed_words_is_a_count_field():
    assert "transcribed_words" in corpus_counts.COUNT_FIELDS
