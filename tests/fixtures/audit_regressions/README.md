# Audit-finding regression fixtures

Every audit finding that led to a FormosanBank *code* fix gets a minimal
fixture here plus one test, named after the finding:

    <yyyy-mm>-<corpus-slug>-<finding-slug>.xml
    e.g. 2026-08-ntu-rukai-starred-parens.xml

Convention (also stated in the `audit-dev-repo` skill, step 6): the audit's
remediation is not complete until the fixture and its test exist. Fixtures
stay minimal — one TEXT, only the elements the finding needs. Findings fixed
in a *dev repo's* build scripts (not in FormosanBank code) do not belong
here; they belong in that repo's own tests.
