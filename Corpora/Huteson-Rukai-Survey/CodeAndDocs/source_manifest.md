# Private source manifest

The source files are not tracked. Retrieve the attachments from Basecamp card
`8255603132` and place them at:

- `Private/source/basecamp/card-8255603132/huteson_2003_rukai_survey.pdf`
- `Private/source/basecamp/card-8255603132/source_license_screenshot_2025-01-24.png`

Create the text cache with:

```bash
mkdir -p Private/cache
pdftotext -layout \
  Private/source/basecamp/card-8255603132/huteson_2003_rukai_survey.pdf \
  Private/cache/huteson_2003_rukai_survey.layout.txt
```

Expected SHA-256 values:

- PDF: `adf8c6124f46ed414c61c7d121fab22f489c6b98fb17dcd584dbc2eac210b91f`
- licence screenshot: `e308f3a55cd605ed8c59de0748131034c12fd09f7e2349845985952fdb0ddff4`
- layout text: `eaa82f21c539b3f0f9c4cc0caa50f044947fc82e197d25b015d254778a4d062b`
