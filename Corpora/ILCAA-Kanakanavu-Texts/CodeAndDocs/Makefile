PYTHON ?= python3

.PHONY: verify generate audit test digest reproduce

generate:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/pipeline.py all --config scripts/config.yaml

audit:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/source_xml_audit.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m pytest -q

digest:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/reproduction_digest.py

reproduce:
	PYTHON=$(PYTHON) scripts/reproduce.sh

verify: generate audit test
