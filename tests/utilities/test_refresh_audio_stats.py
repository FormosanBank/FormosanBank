# tests/utilities/test_refresh_audio_stats.py
import importlib.util, wave, struct
from pathlib import Path

def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[2] / "QC" / "utilities" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

refresh = _load("refresh_audio_stats")
audio_durations = _load("audio_durations")


def test_refresh_runs_steps_and_deletes_audio(tmp_path):
    corpus = tmp_path / "Corpora" / "Mini"
    xml_dir = corpus / "XML" / "Amis"; xml_dir.mkdir(parents=True)
    (xml_dir / "a.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="standard">w</FORM><AUDIO file="a.wav"/></S></TEXT>',
        encoding="utf-8")
    (tmp_path / "statistics").mkdir()
    (tmp_path / "statistics" / "Mini_corpora_stats.csv").write_text(
        "language,dialect,segmented_words,glossed_words,transcribed_audio_count,"
        "transcribed_audio_seconds,untranscribed_audio_count,untranscribed_audio_seconds,"
        "eng_transl_count,zho_transl_count,word_count,file_count,sentences,word_elements,"
        "morpheme_elements,translation_elements,audio_elements,parse_errors\n"
        "ami,Coastal,0,0,1,0.0,0,0.0,0,0,1,1,1,0,0,0,1,0\n", encoding="utf-8")

    def fake_download(corpus_dir):
        ad = corpus_dir / "Audio" / "Amis"; ad.mkdir(parents=True)
        with wave.open(str(ad / "a.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
            w.writeframes(struct.pack("<8000h", *([0] * 8000)))

    rc = refresh.refresh_corpus(corpus, keep_audio=False,
                                download=fake_download, regen_stats=lambda d: None,
                                computed_at="2026-06-12")
    assert rc == 0
    rows = audio_durations.load_for_corpus(tmp_path / "statistics", "Mini")
    assert rows[("ami", "Coastal")]["transcribed_audio_seconds"] == 1.0
    assert rows[("ami", "Coastal")]["transcribed_audio_count"] == 1
    assert not (corpus / "Audio").exists()  # deleted (keep_audio=False)
