def test_cli_main_exists():
    from QC.utilities.dialect_detector_pkg.cli import main
    assert callable(main)
