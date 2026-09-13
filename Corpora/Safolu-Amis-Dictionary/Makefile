.PHONY: all sources rebuild verify test

PYTHON ?= python3
FB ?= ../FormosanBank
VALIDATOR_PYTHON ?= $(FB)/.venv/bin/python3

all: rebuild

sources:
	$(PYTHON) scripts/fetch_sources.py

rebuild:
	VALIDATOR_ROOT=$(FB) VALIDATOR_PYTHON=$(VALIDATOR_PYTHON) SOURCES_DIR=$(SOURCES_DIR) REPORT_DIR=$(REPORT_DIR) scripts/rebuild_xml.sh

verify:
	$(PYTHON) scripts/verify_handoff.py
	$(PYTHON) scripts/audit_issue_1.py

test:
	$(PYTHON) -m unittest discover -s tests -v
