# Formosan Audit Report

- Formosan repo audit tool: PASS for this repository, 0 errors and 0 warnings.
- Audit report JSON: `logs/formosan_repo_audit_current_after.json`.
- FormosanBank QC XML validation: PASS, 0 issues.
- FormosanBank QC gloss validation with `--check_morpho`: no W-count mismatches. The M-count heuristic reports 21 expected infix reanalysis cases where one source W form is intentionally represented as a discontinuous base M plus an infix M; details are in `logs/formosan_qc/glosses/validation_m_mismatches.csv`.
- FormosanBank punctuation/standardization validation: PASS.
- Remediation applied: final XML is in `Final_XML/Truku/` while keeping `xml:lang="trv"`; original S/W forms preserve source segmentation, sentence-level standard forms remove segmentation/null/parenthetical markers conservatively, morpheme-level gloss translations are emitted only when source gloss parts align reliably, slash alternatives are preserved with starred alternatives omitted, and parenthesized examples are retained and flagged for manual QC.

Commands:

```bash
python3 /Users/hunterschep/FormosanBankRepos/Formosan-Repo-Audit/formosan_repo_audit.py <temp-parent-containing-symlink-to-this-repo> --json logs/formosan_repo_audit_current_after.json --max-issues 50 --no-fail
python3 /Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_xml.py by_path --path Final_XML --verbose --log_dir logs/formosan_qc
python3 /Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_glosses.py Final_XML --check_morpho --output_dir logs/formosan_qc/glosses
python3 /Users/hunterschep/FormosanBankRepos/FormosanBank/QC/validation/validate_punct.py by_path --path Final_XML --verbose --log_dir logs/formosan_qc
```
