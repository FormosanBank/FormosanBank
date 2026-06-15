.PHONY: formosanbank all sources safolu validate qc check-final-xml-only clean-sources

PYTHON ?= python3
# FormosanBank sibling repo, where the shared QC tools live.
FB ?= ../FormosanBank

SAFOLU_DIR = Final_XML/Amis/Safolu
SAFOLU_XML = $(SAFOLU_DIR)/amis_safolu_examples.xml

formosanbank all: sources safolu

sources:
	$(PYTHON) scripts/fetch_sources.py

safolu: sources
	$(PYTHON) scripts/build_formosanbank_xml.py
	$(MAKE) validate

validate:
	$(PYTHON) scripts/validate_formosanbank_xml.py $(SAFOLU_XML)
	$(PYTHON) scripts/audit_source_coverage.py
	$(MAKE) check-final-xml-only

# QC enrichment. Run AFTER `make safolu`/`make build`: the build emits only the
# original tier; this adds the standard tier + IPA PHON in place, using the
# FormosanBank QC tools (Ortho113 for Amis). Order matters: clean_xml is run
# before AND after standardization, and add_phonology only after both.
# Re-running the build resets the XML to original-tier-only, so re-run `make qc`
# after any rebuild.
qc:
	$(PYTHON) $(FB)/QC/cleaning/clean_xml.py      --corpora_path $(SAFOLU_DIR)
	$(PYTHON) $(FB)/QC/utilities/standardize.py   --copy --corpora_path $(SAFOLU_DIR)
	$(PYTHON) $(FB)/QC/cleaning/clean_xml.py      --corpora_path $(SAFOLU_DIR)
	$(PYTHON) $(FB)/QC/utilities/add_phonology.py --corpora_path $(SAFOLU_DIR)
	@mkdir -p qc-logs && mv -f $(SAFOLU_DIR)/cleaner_warnings.csv qc-logs/ 2>/dev/null || true
	# Remove duplicate example sentences (the same example reused under related
	# headwords). Compares the standard tier; keeps the first of each group.
	$(PYTHON) $(FB)/QC/cleaning/remove_duplicate_sentences.py by_path --path $(SAFOLU_DIR) --apply
	$(PYTHON) $(FB)/QC/validation/validate_xml.py  by_path --path $(SAFOLU_DIR) --no-exit-on-hard
	$(PYTHON) $(FB)/QC/validation/validate_text.py by_path --path $(SAFOLU_DIR) --no-exit-on-hard
	$(MAKE) check-final-xml-only

check-final-xml-only:
	@test -z "$$(find Final_XML -type f ! -name '*.xml' -print)" || (echo "Final_XML contains non-XML files:"; find Final_XML -type f ! -name '*.xml' -print; exit 1)

clean-sources:
	rm -rf _sources
