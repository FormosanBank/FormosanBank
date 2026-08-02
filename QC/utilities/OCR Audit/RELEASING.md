# Releasing reviewOCR

Short version: **commit the source, publish the binaries.** As of 2026-08,
`*.exe`, `*.pyz`, and `*.app/` are in the repo's [.gitignore](../../../.gitignore),
so built applications are no longer tracked. Ship them as **GitHub Release
assets** instead.

## Why

Git stores every version of every binary forever. Six commits of
`reviewOCR.exe` meant six separate ~10 MB blobs that everyone who clones
FormosanBank has to download — permanently, even after the files are deleted.
Release assets live outside the git object store, so they cost nothing to
people who only want the corpora.

The files still in the repo are the ones that *should* be: `reviewOCR.py`
(the source), `reviewOCR.spec` (the build recipe), `README.md`, and the
starter `data/` folder.

## Build

From this directory, with the project venv active:

```bash
pip install pyinstaller
pyinstaller reviewOCR.spec
```

Output lands in `dist/` (Windows/Linux) or `macos dist/` (macOS). Both are
now gitignored, so nothing will show up in `git status` — that is expected.

PyInstaller cannot cross-compile. **A Windows `.exe` must be built on
Windows and a macOS `.app` on macOS**, so a release with both needs two
machines (or a VM).

## Package the assets

The app will not run unless the `data/` folder sits next to it, so bundle
them together rather than uploading a bare executable.

**Windows** — put `reviewOCR.exe` and `data/` in one folder and zip it:

```
reviewOCR-1.3-windows.zip
├── reviewOCR.exe
└── data/{lastsession.json, errors.csv, errorFreq.csv, allText.csv}
```

**macOS** — use `ditto`, not Finder's "Compress" and not `zip`. A plain
`zip` drops the executable bit and symlinks inside the `.app` bundle, and
the result won't launch on the other end:

```bash
ditto -c -k --sequesterRsrc --keepParent "macos dist/reviewOCR.app" reviewOCR-1.3-macos.zip
```

Then add `data/` to that zip, or ship it as a second asset.

## Publish

**Web UI:** Releases → "Draft a new release" → "Choose a tag" → type a new
tag → set target `main` → drag the zips into the assets box → Publish.

**CLI** (needs `gh auth login` once):

```bash
gh release create ocr-audit-v1.3 \
  --title "OCR Audit v1.3" \
  --notes "Adds unit type to XML tags; allText moved to data/allText.csv." \
  reviewOCR-1.3-windows.zip \
  reviewOCR-1.3-macos.zip
```

Tag convention: `ocr-audit-vX.Y`. Prefixing with the tool name keeps these
from colliding with any future corpus- or repo-level release tags.

To add a binary to a release that already exists:

```bash
gh release upload ocr-audit-v1.3 reviewOCR-1.3-macos.zip
```

## Warn users about the OS security prompts

Neither build is code-signed, so both operating systems will object. Put
this in the release notes:

- **macOS:** "reviewOCR cannot be opened because the developer cannot be
  verified." Fix: right-click (or Control-click) the app → **Open** →
  **Open** again. Only needed the first time. If macOS refuses outright,
  run `xattr -d com.apple.quarantine /path/to/reviewOCR.app`.
- **Windows:** SmartScreen shows "Windows protected your PC." Fix:
  **More info** → **Run anyway**.

## Checklist

- [ ] Bump the version in the Version History section of [README.md](README.md)
- [ ] Build on Windows; build on macOS
- [ ] Zip each with `data/` (`ditto` for the `.app`)
- [ ] `gh release create ocr-audit-vX.Y …` with both assets
- [ ] Release notes include the changelog and the Gatekeeper/SmartScreen steps
- [ ] Confirm the download link in the [root README](../../../README.md) still resolves
