"""validate_audio_quality.py — score each (audio, transcript) pair on 4 MT metrics.

Port of Jacob Ye's `compute_metrics.py` from
`Formosan-ILRDF_Dicts/data_validation/` into FormosanBank.

For each <S> in the corpus that has both <FORM> and <AUDIO file="...">,
produce four mismatch scores:

  ctc_score: mean per-frame posterior of forced CTC alignment
             (wav2vec2 BASE_960H, English). Higher = better alignment.
  wer / cer: word- and character-error-rate between transcript and
             greedy CTC decode of the same wav2vec2 emissions.
             Lower = better. (Off-the-shelf English model, so
             absolute values are meaningless — relative ranking
             within a language is the signal.)
  pdm_score: Levenshtein ratio between the orthographic transcript and
             an Allosaurus universal-phoneme transcription.
             Higher = better.

Usage:
    python QC/validation/validate_audio_quality.py \\
        --corpus_path Corpora/ePark/ \\
        --metrics ctc,wer,cer \\
        --out-csv Corpora/ePark/results/Amis_scores.csv

Outputs a CSV with columns:
  lang, sentence_id, word, audio_path, transcript, asr_hypothesis,
  ctc_score, wer, cer, pdm_score

This script is RESUMABLE: re-running with the same `--out-csv` skips
sentence_ids already present in the file.

Dependencies: heavy. Install via `pip install -r requirements-audio-mt.txt`
(torch, torchaudio, torchcodec, allosaurus, Levenshtein, unidecode).
Also requires a sibling clone of Jacob's `data_quality_eval/` repo for
the CTC alignment helpers — clone at the same parent dir as
FormosanBank, see `QC/README.md` for the exact command.

Schema/layout note: This port walks `<corpus>/XML/` and resolves audio
under `<corpus>/Audio/` (the canonical layout per B9.2). Jacob's
original used `Final_XML`/`Final_audio` — those are no longer
supported here.
"""
import argparse
import csv
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Heavy deps (torch, torchaudio, allosaurus, Levenshtein) are imported
# inside the functions that need them so `--help` works before install.

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_QUALITY_EVAL_SIBLING = _REPO_ROOT.parent / "data_quality_eval"

CHARS_RE = re.compile(r'[\(\)\_\,\?\.\!\-\;\:\"\“\%\‘\”\�\"\[\]\(\)\*=/@\+><\^]')
DIGIT_RE = re.compile(r'\d+')

CSV_HEADER = [
    "lang", "sentence_id", "word", "audio_path", "transcript",
    "asr_hypothesis", "ctc_score", "wer", "cer", "pdm_score",
]

VALID_METRICS = {"ctc", "wer", "cer", "pdm"}


# -----------------------------------------------------------------------------
# Pure helpers (no heavy deps)
# -----------------------------------------------------------------------------

def parse_metrics(s: str) -> set[str]:
    if s == "all":
        return set(VALID_METRICS)
    return {m.strip().lower() for m in s.split(",") if m.strip()}


def clean_for_alignment(raw: str) -> str:
    """ASCII-fold, strip punctuation/digits, return space-separated words."""
    try:
        import unidecode
    except ImportError:
        # Fall back to ASCII-passthrough so tests don't hard-require unidecode.
        unidecode = None
    text = unidecode.unidecode(raw) if unidecode is not None else raw
    text = CHARS_RE.sub('', text)
    text = DIGIT_RE.sub('', text)
    return " ".join(text.split())


def levenshtein_distance(a, b) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            )
        prev = cur
    return prev[-1]


def wer_cer(ref: str, hyp: str):
    ref_clean = ref.strip().lower()
    hyp_clean = hyp.strip().lower()
    if not ref_clean:
        return None, None
    if not hyp_clean:
        return 1.0, 1.0
    ref_words = ref_clean.split()
    hyp_words = hyp_clean.split()
    wer_v = levenshtein_distance(ref_words, hyp_words) / max(1, len(ref_words))
    cer_v = levenshtein_distance(list(ref_clean), list(hyp_clean)) / max(1, len(ref_clean))
    return wer_v, cer_v


# -----------------------------------------------------------------------------
# Corpus walking
# -----------------------------------------------------------------------------

def collect_entries(xml_path: Path, audio_root: Path, lang: str,
                    word_map: dict | None = None) -> list[dict]:
    """Walk the XML, return per-sentence dicts for sentences that have
    both <FORM> and an existing <AUDIO file>."""
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    entries = []
    for s in root.findall("S"):
        audio = s.find("AUDIO")
        form = s.find("FORM")
        if audio is None or form is None:
            continue
        audio_file = audio.attrib.get("file")
        audio_url = audio.attrib.get("url", "")
        text = (form.text or "").strip()
        if not audio_file or not text:
            continue
        # Resolve under audio_root (recursive search as last resort).
        candidate = audio_root / audio_file
        if not candidate.is_file():
            found = next(iter(audio_root.rglob(audio_file)), None)
            if found is None:
                continue
            candidate = found
        entries.append({
            "lang": lang,
            "sentence_id": s.attrib.get("id", ""),
            "word": (word_map or {}).get(audio_url, ""),
            "audio_path": str(candidate),
            "audio_url": audio_url,
            "transcript": text,
        })
    return entries


def collect_corpus(corpus_path: Path, audio_root: Path | None = None,
                   word_map: dict | None = None) -> list[dict]:
    """Walk every XML under <corpus_path>/XML/, return entries.

    `lang` is taken from the XML root's @xml:lang. If `audio_root` is
    None, defaults to `<corpus_path>/Audio/`.
    """
    xml_dir = corpus_path / "XML"
    audio_dir = audio_root if audio_root is not None else (corpus_path / "Audio")
    entries: list[dict] = []
    if not xml_dir.is_dir():
        return entries
    for xml_path in sorted(xml_dir.rglob("*.xml")):
        try:
            tree = ET.parse(str(xml_path))
        except ET.ParseError:
            continue
        root = tree.getroot()
        lang = root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        entries.extend(collect_entries(xml_path, audio_dir, lang, word_map=word_map))
    return entries


def load_existing(out_csv: Path) -> set[str]:
    if not out_csv.exists():
        return set()
    seen: set[str] = set()
    with out_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seen.add(row["sentence_id"])
    return seen


def open_writer(out_csv: Path, columns: list[str]):
    is_new = not out_csv.exists()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    f = out_csv.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=columns)
    if is_new:
        writer.writeheader()
    return f, writer


# -----------------------------------------------------------------------------
# Heavy pipelines (Jacob's port). Imports happen at call time.
# -----------------------------------------------------------------------------

def greedy_ctc_decode(emission, labels) -> str:
    pred_ids = emission.argmax(dim=-1).tolist()
    blank_id = 0  # wav2vec2 BASE_960H convention
    out, prev = [], -1
    for pid in pred_ids:
        if pid != prev and pid != blank_id:
            out.append(labels[pid])
        prev = pid
    return "".join(out).replace("|", " ").strip().lower()


def run_acoustic_pass(entries, want_ctc: bool, want_wer_cer: bool,
                      data_quality_eval_path: Path | None = None):
    """CTC + WER/CER pass over entries. Returns dict keyed by sentence_id."""
    if not (want_ctc or want_wer_cer):
        return {}
    import numpy as np
    import torch
    import torchaudio
    from tqdm import tqdm

    dqe = data_quality_eval_path or _DATA_QUALITY_EVAL_SIBLING
    sys.path.insert(0, str(dqe))
    from utils_CTC import get_trellis, backtrack  # type: ignore

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().to(device)
    labels = bundle.get_labels()
    label_to_id = {c: i for i, c in enumerate(labels)}
    target_sr = bundle.sample_rate

    results: dict[str, dict] = {}
    for entry in tqdm(entries, desc="acoustic", disable=not sys.stderr.isatty()):
        sid = entry["sentence_id"]
        try:
            waveform, sr = torchaudio.load(entry["audio_path"])
            if sr != target_sr:
                waveform = torchaudio.functional.resample(waveform, sr, target_sr)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            with torch.inference_mode():
                emissions, _ = model(waveform.to(device))
                emissions = torch.log_softmax(emissions, dim=-1)
            emission = emissions[0].cpu().detach()
        except Exception as e:
            results[sid] = {"asr_hypothesis": "", "ctc_score": None,
                            "wer": None, "cer": None, "_error": f"audio_load: {e}"}
            continue

        out = {"asr_hypothesis": "", "ctc_score": None, "wer": None, "cer": None}
        if want_wer_cer:
            hyp = greedy_ctc_decode(emission, labels)
            ref = clean_for_alignment(entry["transcript"])
            w, c = wer_cer(ref, hyp)
            out["asr_hypothesis"] = hyp
            out["wer"] = w
            out["cer"] = c
        if want_ctc:
            ref_clean = clean_for_alignment(entry["transcript"]).upper()
            transcript = "|" + "|".join(ref_clean.split()) + "|"
            tokens = [label_to_id[c] for c in transcript if c in label_to_id]
            if len(tokens) >= 2 and emission.size(0) >= len(tokens):
                try:
                    trellis = get_trellis(emission, tokens)
                    path = backtrack(trellis, emission, tokens)
                    if path is not None:
                        out["ctc_score"] = float(np.mean([p.score for p in path]))
                except Exception as e:
                    out["_ctc_error"] = str(e)
        results[sid] = out
    return results


def run_pdm_pass(entries, cache_path: Path | None = None):
    """PDM (Allosaurus-based phoneme matching) pass. Returns dict keyed by sentence_id."""
    try:
        from allosaurus.app import read_recognizer
        from Levenshtein import ratio
        import unidecode
        from tqdm import tqdm
        import torchaudio
    except ImportError as e:
        raise SystemExit(
            "PDM requires `allosaurus`, `Levenshtein`, `unidecode`, `tqdm`, "
            "`torchaudio`. Install via: pip install -r requirements-audio-mt.txt\n"
            f"(import error: {e})"
        )

    import pickle
    import tempfile

    cache: dict[str, str] = {}
    if cache_path is not None and cache_path.exists():
        with cache_path.open("rb") as f:
            cache = pickle.load(f)

    model = read_recognizer()

    def recognize(ap: str) -> str:
        waveform, sr = torchaudio.load(ap)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tmp_path = tf.name
        try:
            torchaudio.save(tmp_path, waveform, 16000,
                            encoding="PCM_S", bits_per_sample=16)
            return model.recognize(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    results: dict[str, dict] = {}
    for entry in tqdm(entries, desc="pdm", disable=not sys.stderr.isatty()):
        ap = entry["audio_path"]
        if ap in cache:
            phones = cache[ap]
        else:
            try:
                phones = recognize(ap)
            except Exception as e:
                results[entry["sentence_id"]] = {"pdm_score": None,
                                                  "_error": f"allosaurus: {e}"}
                continue
            cache[ap] = phones

        ref = entry["transcript"]
        ref_clean = CHARS_RE.sub('', ref).replace(" ", "")
        ref_ascii = DIGIT_RE.sub('', unidecode.unidecode(ref_clean)).lower()
        phone_stream = unidecode.unidecode(phones).replace(" ", "").lower()
        if not ref_ascii or not phone_stream:
            results[entry["sentence_id"]] = {"pdm_score": None}
            continue
        results[entry["sentence_id"]] = {"pdm_score": float(ratio(phone_stream, ref_ascii))}

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as f:
            pickle.dump(cache, f)
    return results


def write_rows(out_csv: Path, entries: list[dict], acoustic: dict, pdm: dict,
               metrics: set[str], include_pdm: bool) -> None:
    """Materialize the per-entry score rows into out_csv (append-mode)."""
    columns = list(CSV_HEADER)
    if not include_pdm:
        columns = [c for c in columns if c != "pdm_score"]
    f, writer = open_writer(out_csv, columns)
    try:
        for entry in entries:
            sid = entry["sentence_id"]
            row = {c: "" for c in columns}
            row["lang"] = entry["lang"]
            row["sentence_id"] = sid
            row["word"] = entry.get("word", "")
            row["audio_path"] = entry["audio_path"]
            row["transcript"] = entry["transcript"]
            a = acoustic.get(sid, {})
            row["asr_hypothesis"] = a.get("asr_hypothesis", "") or ""
            if a.get("ctc_score") is not None:
                row["ctc_score"] = f"{a['ctc_score']:.6f}"
            if "wer" in metrics and a.get("wer") is not None:
                row["wer"] = f"{a['wer']:.6f}"
            if "cer" in metrics and a.get("cer") is not None:
                row["cer"] = f"{a['cer']:.6f}"
            if include_pdm:
                pscore = pdm.get(sid, {}).get("pdm_score")
                if pscore is not None:
                    row["pdm_score"] = f"{pscore:.6f}"
            writer.writerow(row)
    finally:
        f.close()


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--corpus_path", required=True, type=Path,
                   help="root of the corpus; contains XML/ and Audio/")
    p.add_argument("--out-csv", required=True, type=Path,
                   help="output CSV path (resumable across runs)")
    p.add_argument("--metrics", default="all",
                   help="comma-separated subset of {ctc,wer,cer,pdm}, or 'all'")
    p.add_argument("--sample", type=int, default=0,
                   help="random sample of N entries (0 = all)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--word-map", type=Path, default=None,
                   help="optional pickle: audio_url → headword")
    p.add_argument("--pdm-cache", type=Path, default=None,
                   help="optional pickle cache for Allosaurus outputs (one per language)")
    p.add_argument("--data-quality-eval", type=Path, default=None,
                   help=f"path to Jacob's data_quality_eval clone "
                        f"(default: {_DATA_QUALITY_EVAL_SIBLING})")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    metrics = parse_metrics(args.metrics)
    if not metrics or not metrics.issubset(VALID_METRICS):
        print(f"--metrics must be a subset of {sorted(VALID_METRICS)} (got {metrics})",
              file=sys.stderr)
        return 2

    word_map = None
    if args.word_map is not None and args.word_map.is_file():
        import pickle
        with args.word_map.open("rb") as f:
            word_map = pickle.load(f)

    entries = collect_corpus(args.corpus_path, word_map=word_map)
    if not entries:
        print(f"No entries found under {args.corpus_path}/XML/ with audio.",
              file=sys.stderr)
        return 0

    already = load_existing(args.out_csv)
    if already:
        entries = [e for e in entries if e["sentence_id"] not in already]
        print(f"resuming: {len(already)} already scored, {len(entries)} remaining",
              file=sys.stderr)

    if args.sample and len(entries) > args.sample:
        rng = random.Random(args.seed)
        entries = rng.sample(entries, args.sample)
        print(f"sampled {len(entries)} entries (seed={args.seed})", file=sys.stderr)

    if not entries:
        print("nothing to do.", file=sys.stderr)
        return 0

    acoustic = run_acoustic_pass(
        entries,
        want_ctc=("ctc" in metrics),
        want_wer_cer=bool({"wer", "cer"} & metrics),
        data_quality_eval_path=args.data_quality_eval,
    )
    pdm = {}
    if "pdm" in metrics:
        pdm = run_pdm_pass(entries, cache_path=args.pdm_cache)

    write_rows(args.out_csv, entries, acoustic, pdm,
               metrics=metrics, include_pdm=("pdm" in metrics))
    print(f"wrote {len(entries)} rows → {args.out_csv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
