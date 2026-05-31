"""CorpusIndex: the cross-file accumulator built in pass 1.

The validator runner makes one parse pass over every file in the
target, collecting per-file structured data into a CorpusIndex.
Pass 2 then applies cross-file rules (V081 id uniqueness, …) with
the populated index as their third argument.

Fields:
  ids: TEXT/@id -> list of (path, location-str). location-str is the
       in-file pinpoint (currently always "TEXT" for the root, but
       reserved for future per-W/per-M ids if those ever participate
       in cross-file uniqueness).
  langs: path -> resolved xml:lang for that file's <TEXT> root.
  published_ids: TEXT/@id -> list of paths in published Corpora/.
       Used for V081 cross-corpus id uniqueness. Empty dict if the
       Corpora/ root does not exist (graceful CI handling).
"""
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


@dataclass(frozen=True)
class CorpusIndex:
    ids: dict[str, list[tuple[Path, str]]]
    langs: dict[Path, str]
    published_ids: dict[str, list[Path]]


def build_current_index(file_paths: list[Path]) -> tuple[dict, dict]:
    """Walk file_paths, extracting TEXT/@id and xml:lang for the current
    corpus-under-test (pass 1 collection). Returns (ids, langs).
    Files that fail to parse are silently skipped — the runner reports
    parse errors separately via v000.
    """
    ids: dict[str, list[tuple[Path, str]]] = {}
    langs: dict[Path, str] = {}
    for path in file_paths:
        try:
            tree = etree.parse(str(path))
        except etree.XMLSyntaxError:
            continue
        root = tree.getroot()
        if root.tag != "TEXT":
            continue
        text_id = root.get("id")
        if text_id:
            ids.setdefault(text_id, []).append((path, "TEXT"))
        lang = root.get(_XML_LANG)
        if lang:
            langs[path] = lang
    return ids, langs


def build_published_index(corpora_root: Path) -> dict[str, list[Path]]:
    """Walk each corpus's canonical XML/ subdirectory under corpora_root
    (typically <repo>/Corpora/) extracting TEXT/@id from each .xml file.
    Returns id -> [paths]. Used for cross-corpus id uniqueness check (V081).
    Files that fail to parse are silently skipped.

    Only the canonical `<corpus>/XML/` subdirectory is walked for each
    corpus; working files under `CodeAndDocs/` are NOT considered
    published and would otherwise produce false V081 collisions (e.g.,
    Glosbe's reference_amis/Amis.xml is a working file, not published
    data with the published id 'Amis').

    Returns an empty dict if corpora_root does not exist (gracefully
    handles CI environments without Corpora/).
    """
    if not corpora_root.exists():
        return {}
    result: dict[str, list[Path]] = {}
    for child in sorted(corpora_root.iterdir()):
        if not child.is_dir():
            continue
        xml_subdir = child / "XML"
        if not xml_subdir.is_dir():
            continue
        for xml_path in sorted(xml_subdir.rglob("*.xml")):
            try:
                tree = etree.parse(str(xml_path))
            except etree.XMLSyntaxError:
                continue
            root = tree.getroot()
            if root.tag != "TEXT":
                continue
            text_id = root.get("id")
            if text_id:
                result.setdefault(text_id, []).append(xml_path)
    return result
