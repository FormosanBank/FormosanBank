#!/usr/bin/env bash
# build.sh — regenerate NTUFormosanCorpus XML/ from the source JSONs.
#
# The JSONs under ../grammar, ../sentence and ../story are the starting point
# for this corpus; nothing is scraped, so there is no refresh step. This
# script is the whole build: JSON -> XML/{Grammar,Sentences,Stories}.
#
# Usage:
#   ./build.sh [grammar|sentences|stories|all]     (default: all)
#
# Environment:
#   PYTHON     interpreter to use (default: <bank>/.venv/bin/python)
#   CTABLES    conversion-table dir (default: <bank>/Orthographies/ConversionTables)
#   FB_DIALECTS  dialects.csv to resolve dialect/glottocode (default: <bank>/dialects.csv)
#   NTU_BUILD_OUT  install here instead of ../../XML (trial builds; XML/ untouched)
#   NTU_BUILD_CHECKPOINT=pre-cleanup
#              skip the clean-up steps -- remove_empty_translations and the prune
#              of unsupported W/M tiers. They exist
#              to deal with what could not be fixed, so a trial of a *fix* is
#              compared before them (qa/try_gloss_shift_repairs.sh does this).
#              Never publish a checkpoint build.
#
# Each subcorpus runs the same three phases:
#   A. builder      pipeline_{grammar,sentences,stories}.py: JSON -> XML
#   B. repairs      shared FormosanBank cleaning + the corpus repair scripts
#   C. tiers        punctuation morphemes, prune, id alignment, standard tier + PHON (Ortho94)
#
# Every phase is idempotent; rerunning is safe.

set -euo pipefail

WHICH="${1:-all}"

PIPE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # .../CodeAndDocs/pipeline
CODEDOCS="$(dirname "$PIPE")"
CORPUS="$(dirname "$CODEDOCS")"
BANK="$(cd "$CORPUS/../.." && pwd)"
SCR="$CODEDOCS/scripts"
XML="${NTU_BUILD_OUT:-$CORPUS/XML}"
CHECKPOINT="${NTU_BUILD_CHECKPOINT:-}"
case "$CHECKPOINT" in ""|pre-cleanup) ;; *) echo "unknown NTU_BUILD_CHECKPOINT: $CHECKPOINT" >&2; exit 2 ;; esac

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
export PYTHONPATH="$BANK${PYTHONPATH:+:$PYTHONPATH}"
export FB_DIALECTS="${FB_DIALECTS:-$BANK/dialects.csv}"
CTABLES="${CTABLES:-$BANK/Orthographies/ConversionTables}"

step() { printf '\n=== %s ===\n' "$*"; }
run()  {
  step "$1"; shift
  # tail -0 would close the pipe early and make Python exit 120 on the
  # broken stdout; send discarded output to /dev/null instead.
  if [[ "${TAIL:-2}" == 0 ]]; then "$PY" "$@" >/dev/null 2>&1
  else "$PY" "$@" 2>&1 | tail -"${TAIL:-2}"; fi
}

# ---------------------------------------------------------------- phase B
# Shared cleaning + the repair scripts that every subcorpus needs.
common_repairs() {   # $1 = work dir
  local W="$1"
  run "clean_xml"              "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$W"
  TAIL=0 run "normalize_serialization (lxml)" "$SCR/normalize_serialization.py" --style lxml "$W"
  run "repair_s_gloss_shift"   "$PIPE/repair_s_gloss_shift.py" --xml_dir "$W"
  TAIL=40 run "borrow_shift_blank_glosses" "$PIPE/borrow_shift_blank_glosses.py" --xml_dir "$W" \
      --codedocs "$CODEDOCS" --subcorpus grammar --report "$CORPUS/logs/gloss_shift_borrowed_Grammar.tsv"
}

# ---------------------------------------------------------------- phase C
# Tier construction, shared by all three subcorpora.
finish_tiers() {     # $1 = work dir, $2 = subcorpus name (for report file names)
  local W="$1" SUB="$2"
  run "resolve_slash_alternatives" "$PIPE/resolve_slash_alternatives.py" --xml_dir "$W"
  # Punctuation-only morphemes (ruling 2026-09-28): a repair, not clean-up.
  # Escalations -- cases the rule does not resolve -- go to logs/ for review.
  # These two print every counter (TAIL=40): the 2026-09-08 ruling asks for
  # the numbers withdrawn or rebuilt to be reported, and tail -2 hid them.
  TAIL=40 run "drop_punctuation_morphemes" "$PIPE/drop_punctuation_morphemes.py" --xml_dir "$W" \
      --report "$CORPUS/logs/punctuation_morpheme_escalations_${SUB}.tsv"
  TAIL=40 cleanup "prune non-conforming W/M"   "$PIPE/apply_prune_and_mirror.py" --xml_dir "$W"
  run_opt "mark_original_glosses"   "$SCR/mark_original_glosses.py" --xml-dir "$W"
  run "align_ids"                  "$PIPE/align_ids.py" --xml_dir "$W"
  step "standard tier + PHON (Ortho94)"
  "$PIPE/run_standard_and_phon.sh" "$W" "$CTABLES" 2>&1 | tail -4
}

# A clean-up step: skipped at the pre-cleanup checkpoint (see the header).
cleanup() {
  if [[ "$CHECKPOINT" == pre-cleanup ]]; then step "$1 (skipped: pre-cleanup checkpoint)"; return 0; fi
  run "$@"
}

# mark_original_glosses is witness-gated and conservatively skips files whose
# tier vintage it cannot confirm; a skip is not an error here.
run_opt() { step "$1 (tolerated)"; shift; "$PY" "$@" 2>&1 | tail -1 || true; }

install_into() {     # $1 = work dir, $2 = XML subdir name
  step "install -> XML/$2"
  rm -rf "${XML:?}/$2"
  mkdir -p "$XML/$2"
  # Only the XML is published; the cleaning scripts also drop report CSVs
  # (cleaner_warnings.csv, quote_corrections.csv) into the work dir, and those
  # belong with the logs, not in the corpus.
  cp -r "$1/." "$XML/$2/"
  find "$XML/$2" -type f ! -name '*.xml' -delete
  echo "  $(find "$XML/$2" -name '*.xml' | wc -l) file(s)"
}

build_grammar() {
  local W; W="$(mktemp -d)"; trap 'rm -rf "$W"' RETURN
  step "GRAMMAR: builder (pipeline_grammar.py)"
  "$PY" "$PIPE/pipeline_grammar.py" --json "$CODEDOCS/grammar" --out "$W" \
        --steps 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,21,22 2>&1 | tail -3
  common_repairs "$W"
  run "convert_infix_notation"          "$SCR/convert_infix_notation.py" --xml_dir "$W"
  run "split_optional_parentheticals"   "$SCR/split_optional_parentheticals.py" --xml_dir "$W"
  run "resolve_inline_parentheticals"   "$SCR/resolve_inline_parentheticals.py" --xml_dir "$W"
  cleanup "remove_empty_translations"   "$SCR/remove_empty_translations.py" --xml-dir "$W"
  run "propagate_clitic_boundaries"     "$SCR/propagate_clitic_boundaries.py" --xml_dir "$W"
  finish_tiers "$W" Grammar
  install_into "$W" Grammar
}

# Sentences and Stories share a builder shape and the same repair chain.
build_flat() {       # $1 = sentences|stories
  local kind="$1" W json out builder steps
  W="$(mktemp -d)"; trap 'rm -rf "$W"' RETURN
  case "$kind" in
    sentences) json="$CODEDOCS/sentence"; out=Sentences; builder=pipeline_sentences.py
               steps=0,1,2,3,4,5,7,8,9,10,11,14,15,18 ;;
    stories)   json="$CODEDOCS/story";    out=Stories;  builder=pipeline_stories.py
               steps=0,1,2,3,4,5,7,8,9,10,11,14,15,16,18 ;;
  esac
  step "${out^^}: builder ($builder)"
  "$PY" "$PIPE/$builder" --json "$json" --out "$W" --steps "$steps" 2>&1 | tail -3
  run "clean_xml"              "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$W"
  TAIL=0 run "normalize_serialization (lxml)" "$SCR/normalize_serialization.py" --style lxml "$W"
  run "repair_l2_markers"      "$SCR/repair_l2_markers.py" --xml_dir "$W"
  run "borrow_segmentation"    "$SCR/borrow_segmentation.py" --xml_dir "$W" --source_dir "$CODEDOCS"
  run "repair_s_gloss_shift"   "$PIPE/repair_s_gloss_shift.py" --xml_dir "$W"
  TAIL=40 run "borrow_shift_blank_glosses" "$PIPE/borrow_shift_blank_glosses.py" --xml_dir "$W" \
      --codedocs "$CODEDOCS" --subcorpus "$(basename "$json")" --report "$CORPUS/logs/gloss_shift_borrowed_${out}.tsv"
  run "uniquify_sentence_ids"  "$SCR/uniquify_sentence_ids.py" --xml_dir "$W"
  run "remove_annotation_codes" "$SCR/remove_annotation_codes.py" --xml_dir "$W" --source_dir "$CODEDOCS"
  run "fix_double_encoded_glosses"      "$SCR/fix_double_encoded_glosses.py" --xml_dir "$W"
  run "convert_infix_notation"          "$SCR/convert_infix_notation.py" --xml_dir "$W"
  run "collapse_gloss_only_alternations" "$SCR/collapse_gloss_only_alternations.py" --xml_dir "$W"
  run "resolve_residual_optional_parens" "$SCR/resolve_residual_optional_parens.py" --xml_dir "$W"
  run "split_optional_parentheticals"   "$SCR/split_optional_parentheticals.py" --xml_dir "$W"
  cleanup "remove_empty_translations"   "$SCR/remove_empty_translations.py" --xml-dir "$W"
  run "propagate_clitic_boundaries"      "$SCR/propagate_clitic_boundaries.py" --xml_dir "$W"
  finish_tiers "$W" "$out"
  install_into "$W" "$out"
}

case "$WHICH" in
  grammar)   build_grammar ;;
  sentences) build_flat sentences ;;
  stories)   build_flat stories ;;
  all)       build_grammar; build_flat sentences; build_flat stories ;;
  *) echo "usage: $0 [grammar|sentences|stories|all]" >&2; exit 2 ;;
esac

step "done"
