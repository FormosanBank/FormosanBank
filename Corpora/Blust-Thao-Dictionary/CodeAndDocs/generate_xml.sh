#!/usr/bin/env bash
# THE entry point (POL-047): source records -> published XML/.
#
#   1a. build_xml.py --texts-only         corpus-local; the five interlinear
#                                         texts. FIRST: it replaces its output
#                                         directory atomically.
#   1b. build_entry_xml.py                corpus-local; the headword entries and
#                                         the example sentences, from the schema
#                                         parse. Additive, so it goes second.
#   2. QC/cleaning/apply_manual_edits.py  no-op (this corpus records none)
#   3. QC/cleaning/clean_xml.py
#   4. QC/utilities/standardize.py        --tsv_path Thao_Blust2003_113.tsv
#   5. QC/utilities/add_phonology.py      --orthography Blust2003
#   6a. prefer_the_etymology.py           corpus-local; among identical
#                                         entries keep the one carrying the
#                                         etymology, so 6b cannot lose it
#   6b. QC/cleaning/remove_duplicate_sentences.py --scope corpus --apply
#                                         POL-022: a reference resource dedups
#   6c. apply_same_form_rulings.py        corpus-local; the maintainer's
#                                         verdicts on the groups 6b cannot
#                                         touch - same FORM, different gloss
#
# Build only: no validator runs here. See CodeAndDocs/validate.sh.
#
set -euo pipefail
exec python3 "$(dirname "$0")/regenerate.py" "$@"
