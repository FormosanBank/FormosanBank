"""Make CodeAndDocs/ importable however the suite is invoked.

`unittest discover -s CodeAndDocs/tests` and a whole-directory pytest run both
happened to work before, but only because another test module inserted the
path first. Running one file on its own failed with ModuleNotFoundError.
"""
import sys
from pathlib import Path

CODE_AND_DOCS = str(Path(__file__).resolve().parents[1])
if CODE_AND_DOCS not in sys.path:
    sys.path.insert(0, CODE_AND_DOCS)
