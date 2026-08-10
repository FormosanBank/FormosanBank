#!/usr/bin/env bash
# make.sh — rerun the full NTUFormosanCorpus processing pipeline.
#
# Executable form of the "Processing" section in ../readme.md: parses the
# source JSONs into CodeAndDocs/Final_XML, runs the shared FormosanBank
# cleaning/standardization/phonology pipeline, installs the result into the
# corpus XML/ directory, then applies the post-processing repair steps 4-20
# in order. Ends with a corpus-wide add_phonology refresh (so PHON is
# canonical even where a repair step's witness-gated regeneration skipped),
# re-application of recorded hand edits (CodeAndDocs/manual_edits.xml, if
# present), and a validate_text summary.
#
# Usage:
#   ./make.sh [--with-audio]
#
#   --with-audio   also download the Grammar/Stories audio (slow; needs
#                  network). XML generation does not require it: AUDIO
#                  elements are removed by sentinel URL, not by checking
#                  files on disk.
#
# Notes:
#   - Step 7 of the README (remove_null_symbols.py) is RETIRED: null
#     morphemes are handled by clean_xml/standardize/add_phonology, and
#     W/M-level standard FORMs must retain the ∅ marker (V069/V124/V125).
#     remove_stress_accents.py is likewise retired (standardize
#     --remove_accents owns accent stripping). Neither is run here.
#   - Step 8 of the README is manual (V121 review); nothing to run.
#     Hand edits belong in CodeAndDocs/manual_edits.xml (captured with
#     QC/utilities/capture_manual_edits.py) so this script can re-apply
#     them after a regeneration.
#   - Per-step PHON regeneration inside steps 5/9/11/12 models the old
#     add_phonology output and will conservatively skip under the current
#     pipeline; the final add_phonology pass here makes PHON canonical.
#   - Every repair step is idempotent; rerunning this script is safe.

set -euo pipefail

WITH_AUDIO=0
for arg in "$@"; do
  case "$arg" in
    --with-audio) WITH_AUDIO=1 ;;
    -h|--help) sed -n '2,35p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg (try --help)" >&2; exit 2 ;;
  esac
done

CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../CodeAndDocs
CORPUS="$(dirname "$CODEDOCS")"                            # corpus root
BANK="$(cd "$CORPUS/../.." && pwd)"                        # FormosanBank root
SCRIPTS="$CODEDOCS/scripts"
FINAL="$CODEDOCS/Final_XML"                                # parser output

PY="${PYTHON:-$BANK/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

step() { printf '\n=== %s ===\n' "$*"; }

step "1. Parse original files -> Final_XML/"
(cd "$CODEDOCS" && "$PY" scripts/run_parsers.py)

if [[ "$WITH_AUDIO" -eq 1 ]]; then
  step "2. Download audio"
  (cd "$CODEDOCS" && "$PY" scripts/download_grammar_audio.py)
  (cd "$CODEDOCS" && "$PY" scripts/download_stories_audio.py)
else
  step "2. Download audio — SKIPPED (pass --with-audio to enable)"
fi

step "2b. Remove no-audio sentinel AUDIO elements"
(cd "$CODEDOCS" && "$PY" scripts/remove_no_audio_elements.py)

step "3a. clean_xml (original-tier cleaning + null-glyph canonicalization)"
"$PY" "$BANK/QC/cleaning/clean_xml.py" --corpora_path "$FINAL"

step "3b. standardize --remove_accents (standard tier: accents, S-level null units, C012)"
"$PY" "$BANK/QC/utilities/standardize.py" --remove_accents --corpora_path "$FINAL"
# standardize writes its c012/c022 warnings next to the XML it processed;
# keep them in CodeAndDocs, not in the published tree.
[[ -f "$FINAL/standardize_warnings.csv" ]] && mv "$FINAL/standardize_warnings.csv" "$CODEDOCS/standardize_warnings.csv"

step "3c. add_phonology (Ortho113)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$FINAL" --orthography Ortho113

run_step() { local label="$1"; shift; step "$label"; "$PY" "$@"; }

# Serialization boundaries (see normalize_serialization.py): step 4's
# round-trip guard expects the parsers' minidom style, steps 5-20 expect
# the published lxml style. Convert at each boundary so no guard skips.
run_step "3d. normalize serialization (minidom, for step 4)" \
    "$SCRIPTS/normalize_serialization.py" --style minidom "$FINAL"
run_step "4. repair_empty_morphemes"            "$SCRIPTS/repair_empty_morphemes.py" --xml_dir "$FINAL"
run_step "4b. normalize serialization (lxml, for steps 5-20)" \
    "$SCRIPTS/normalize_serialization.py" --style lxml "$FINAL"

step "4c. Install Final_XML/ -> XML/"
# No --delete: XML/ also holds per-language failed_audio.csv logs that are
# only regenerated when --with-audio is used. Remove XML/ manually first if
# a file has been renamed away in the parsers.
rsync -a "$FINAL"/ "$CORPUS/XML"/

run_step "5. borrow_segmentation"               "$SCRIPTS/borrow_segmentation.py"
run_step "6. dedupe_sentence_ids"               "$SCRIPTS/dedupe_sentence_ids.py"
step "7. remove_null_symbols — RETIRED (handled by steps 3a-3c; see readme.md)"
step "8. manual V121 review — nothing scripted (hand edits go in manual_edits.xml)"
run_step "9. remove_annotation_codes"           "$SCRIPTS/remove_annotation_codes.py"
run_step "10a. fix_swapped_gloss_langs (stems 63/64)" "$SCRIPTS/fix_swapped_gloss_langs.py"
run_step "10b. fix_swapped_gloss_langs --all"   "$SCRIPTS/fix_swapped_gloss_langs.py" --all
run_step "11. apply_manual_corrections"         "$SCRIPTS/apply_manual_corrections.py"
run_step "12. repair_l2_markers"                "$SCRIPTS/repair_l2_markers.py"
run_step "13. fix_double_encoded_glosses"       "$SCRIPTS/fix_double_encoded_glosses.py"
run_step "14. convert_infix_notation"           "$SCRIPTS/convert_infix_notation.py"
# Step 14's notes: the infix sweep exposed residue handled by the step 11/12
# token maps, so both are re-run after it (idempotent).
run_step "11b. apply_manual_corrections (re-run after 14)" "$SCRIPTS/apply_manual_corrections.py"
run_step "12b. repair_l2_markers (re-run after 14)"        "$SCRIPTS/repair_l2_markers.py"
run_step "15. split_optional_parentheticals"    "$SCRIPTS/split_optional_parentheticals.py"
run_step "16. expand_slash_alternatives"        "$SCRIPTS/expand_slash_alternatives.py"
run_step "17. strip_trailing_slash"             "$SCRIPTS/strip_trailing_slash.py"
run_step "18. expand_word_level_alternatives"   "$SCRIPTS/expand_word_level_alternatives.py"
run_step "19. collapse_gloss_only_alternations" "$SCRIPTS/collapse_gloss_only_alternations.py"
run_step "20. resolve_residual_optional_parens" "$SCRIPTS/resolve_residual_optional_parens.py"

step "Final PHON refresh (canonical add_phonology over the repaired XML)"
"$PY" "$BANK/QC/utilities/add_phonology.py" --corpora_path "$CORPUS/XML" --orthography Ortho113

if [[ -f "$CODEDOCS/manual_edits.xml" ]]; then
  step "Re-apply recorded hand edits (manual_edits.xml)"
  "$PY" "$BANK/QC/cleaning/apply_manual_edits.py" --corpora_path "$CORPUS/XML"
else
  step "No CodeAndDocs/manual_edits.xml — skipping hand-edit re-application"
fi

step "Validation summary (validate_text; HARD findings do not abort)"
"$PY" "$BANK/QC/validation/validate_text.py" by_path --path "$CORPUS/XML" \
  --no-exit-on-hard --log_dir "$CORPUS/logs"

step "Done. Review 'git diff' before committing."
