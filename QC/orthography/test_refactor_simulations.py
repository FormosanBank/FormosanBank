import pickle
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orthography_extract import run_reference_simulations


def test_run_reference_simulations_creates_orthographic_info(tmp_path: Path) -> None:
    corpus_root = tmp_path / "Corpora" / "PaiwanTest"
    corpus_root.mkdir(parents=True)
    xml_path = corpus_root / "sample.xml"
    xml_path.write_text(
        """<root dialect=\"Southern\">
  <S>
    <FORM kindOf=\"standard\">maku aicu</FORM>
    <FORM>maku aicu</FORM>
  </S>
  <S>
    <FORM kindOf=\"standard\">cima aicu</FORM>
  </S>
</root>
""",
        encoding="utf-8",
    )

    output_dir = tmp_path / "references"
    created_dirs = run_reference_simulations(
        language_to_process="Paiwan",
        dialect="Southern",
        corpora_paths=[str(corpus_root)],
        output_dir=str(output_dir),
        num_sim=1,
        ref_ratio=0.5,
        kindOf="standard",
        by_dialect=True,
        verbose=False,
        seed=0,
    )

    assert len(created_dirs) == 1
    info_path = output_dir / "Paiwan" / "Southern" / "partition_1" / "orthographic_info"
    assert info_path.exists()

    with info_path.open("rb") as handle:
        info = pickle.load(handle)

    assert "character_frequency" in info
    assert "word_frequency" in info
