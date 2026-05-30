"""SOFT-severity rules: violations populate the SOFT CSV but do not
affect exit code.

Each rule pre-aggregates per (rule_id, file, language, character).
Returning thousands of un-aggregated Findings per file would flood
the CSV writer.

Signature: same as HARD rules.
"""
from QC.validation._finding import Finding

RULES: list = []
CROSS_FILE_RULES: list = []
