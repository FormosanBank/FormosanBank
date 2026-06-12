# tests/utilities/test_migrate_audio_durations.py
import importlib.util
from pathlib import Path

def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[2] / "QC" / "utilities" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

migrate = _load("migrate_audio_durations")
audio_durations = _load("audio_durations")

PER_CORPUS_HEADER = (
    "language,dialect,segmented_words,glossed_words,transcribed_audio_count,"
    "transcribed_audio_seconds,untranscribed_audio_count,untranscribed_audio_seconds,"
    "eng_transl_count,zho_transl_count,word_count,file_count,sentences,word_elements,"
    "morpheme_elements,translation_elements,audio_elements,parse_errors\n")


def test_build_rows_uses_reference_counts(monkeypatch):
    # Current CSV: count 237, seconds 3034. Reference returns count 158.
    current = PER_CORPUS_HEADER + "pwn,Central,0,0,237,3034.0,0,0.0,0,0,1,1,1,0,0,0,237,0\n"
    def fake_ref(corpus):
        return {("pwn", "Central"): (158, 0)}  # old count from VC
    rows = migrate.build_rows_for_corpus("NTU_Paiwan_ASR", current, fake_ref)
    assert rows[0]["transcribed_audio_seconds"] == 3034.0
    assert rows[0]["transcribed_audio_count"] == 158  # anchor = old VC count -> will read stale


def test_build_rows_skips_zero_audio():
    current = PER_CORPUS_HEADER + "ami,X,0,0,0,0.0,0,0.0,0,0,1,1,1,0,0,0,0,0\n"
    rows = migrate.build_rows_for_corpus("Mini", current, lambda c: {})
    assert rows == []


def test_build_rows_fallback_to_current_when_absent_at_reference():
    current = PER_CORPUS_HEADER + "tay,Sekolik,0,0,666,4242.0,0,0.0,0,0,1,1,1,0,0,0,666,0\n"
    rows = migrate.build_rows_for_corpus("WhitehornCollection", current, lambda c: {})
    assert rows[0]["transcribed_audio_count"] == 666  # fallback: current == old (unchanged)
