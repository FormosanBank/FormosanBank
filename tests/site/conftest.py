"""Make docs/tools importable for the site tests."""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "docs" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
