#!/usr/bin/env python3
"""Parse the three-line Paiwan interlinear source into aligned records."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document


LEGACY_CHARACTERS = str.maketrans(
    {
        "î": "ɫ",
        "ï": "Ɫ",
        "÷": "ḍ",
        "ª": "Ḍ",
    }
)

MORPHEME_BOUNDARY_RE = re.compile(r"([-=]|\s+)")
LETTERS_RE = re.compile(r"[^\wɫⱢḍḌ]+", re.UNICODE)


def normalize_legacy(text: str) -> str:
    """Map the four legacy-font code points used by the Word source."""

    return unicodedata.normalize("NFC", text.translate(LEGACY_CHARACTERS))


def normalized_letters(text: str) -> str:
    """Return a comparison form that keeps letters and digits only."""

    return "".join(char.casefold() for char in text if char.isalnum())


@dataclass(frozen=True)
class AnalysisUnit:
    form: str
    gloss: str
    role: str
    boundary_after: str


@dataclass
class SourceSentence:
    story_number: int
    source_ordinal: int
    printed_label: str
    paragraph_index: int
    natural_cells: list[str] = field(default_factory=list)
    morph_cells: list[str] = field(default_factory=list)
    gloss_cells: list[str] = field(default_factory=list)
    translations: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)

    @property
    def natural_form(self) -> str:
        return normalize_legacy(" ".join(cell for cell in self.natural_cells if cell))

    @property
    def translation(self) -> str:
        return normalize_legacy(" ".join(part for part in self.translations if part))


@dataclass
class SourceStory:
    number: int
    heading: str
    sentences: list[SourceSentence] = field(default_factory=list)

    @property
    def title(self) -> str:
        value = normalize_legacy(self.heading.splitlines()[0].strip())
        return re.sub(r"^\d{3}\s+", "", value)

    @property
    def source_label(self) -> str | None:
        lines = [
            normalize_legacy(line.strip()) for line in self.heading.splitlines()[1:]
        ]
        value = " ".join(line for line in lines if line)
        return value or None


def _cells(text: str, has_label: bool = False) -> list[str]:
    values = text.split("\t")
    if values:
        values = values[1:]
    if has_label:
        return values
    return values


def parse_docx(path: Path) -> list[SourceStory]:
    """Parse the source using paragraph styles and the T-M-G cycle.

    The style name alone cannot distinguish all free translations. In 61
    records Word uses ``InterlineTrans`` for both the third gloss line and the
    following free translation. The parser therefore tracks whether it is
    expecting a morpheme line, gloss line, or post-gloss content.
    """

    document = Document(path)
    stories: list[SourceStory] = []
    story: SourceStory | None = None
    sentence: SourceSentence | None = None
    expected = "text"

    def finish_sentence() -> None:
        nonlocal sentence
        if story is not None and sentence is not None:
            sentence.source_ordinal = len(story.sentences) + 1
            story.sentences.append(sentence)
            sentence = None

    def finish_story() -> None:
        nonlocal story
        if story is not None:
            finish_sentence()
            stories.append(story)
            story = None

    for paragraph_index, paragraph in enumerate(document.paragraphs):
        style = paragraph.style.name
        text = paragraph.text

        if style == "Heading 4" and text.strip():
            finish_story()
            match = re.match(r"\s*(\d{3})\b", text)
            if match is None:
                raise ValueError(
                    f"paragraph {paragraph_index}: malformed story heading"
                )
            story = SourceStory(number=int(match.group(1)), heading=text)
            expected = "text"
            continue

        if story is None:
            continue

        if style == "InterlineText":
            values = text.split("\t")
            label = values[0].strip() if values else ""
            if label:
                finish_sentence()
                sentence = SourceSentence(
                    story_number=story.number,
                    source_ordinal=0,
                    printed_label=label,
                    paragraph_index=paragraph_index,
                )
            if sentence is None:
                raise ValueError(
                    f"story {story.number:03}, paragraph {paragraph_index}: "
                    "continuation before a numbered sentence"
                )
            sentence.natural_cells.extend(values[1:])
            expected = "morph"
            continue

        if sentence is None:
            continue

        if style == "InterlineGlossWithTrans" and expected == "morph":
            sentence.morph_cells.extend(_cells(text))
            expected = "gloss"
            continue

        if style in {"InterlineTrans", "InterlineTransNoFree"} and expected == "gloss":
            sentence.gloss_cells.extend(_cells(text))
            expected = "post_gloss"
            continue

        if style in {
            "InterlineFree",
            "InterlineFreeCommentFollows",
            "Interline Free - Com",
            "InterlineTrans",
            "InterlineTransNoFree",
        }:
            sentence.translations.append(text.strip())
            expected = "post_gloss"
            continue

        if style in {"CommentLastWithHalfSpace", "Comment para + another"}:
            sentence.comments.append(normalize_legacy(text.strip()))
            continue

        if style == "FullTranslation":
            finish_sentence()

    finish_story()

    if [story.number for story in stories] != list(range(1, 101)):
        raise ValueError("source must contain exactly stories 001 through 100")
    sentence_count = sum(len(item.sentences) for item in stories)
    if sentence_count != 2916:
        raise ValueError(f"expected 2,916 source sentences, found {sentence_count}")

    for item in stories:
        for record in item.sentences:
            if not record.translation:
                raise ValueError(
                    f"story {item.number:03} sentence {record.source_ordinal:03}: "
                    "missing free translation"
                )
    return stories


def split_units(morph: str, gloss: str) -> list[AnalysisUnit]:
    """Split one aligned source cell into canonical morpheme units.

    Hyphen, equals, and embedded whitespace all delimit source units. Equals
    marks either an infix or reduplication in this source. A gloss unit
    ``red`` is a reduplicant; every other unit immediately before ``=`` is an
    infix. The caller handles the single source exception whose form and gloss
    have different unit counts.
    """

    morph = normalize_legacy(morph.strip())
    gloss = normalize_legacy(gloss.strip())
    morph_parts = MORPHEME_BOUNDARY_RE.split(morph)
    gloss_parts = MORPHEME_BOUNDARY_RE.split(gloss)
    morph_units = [part.strip() for part in morph_parts[::2] if part.strip()]
    gloss_units = [part.strip() for part in gloss_parts[::2] if part.strip()]
    morph_separators = [part for part in morph_parts[1::2]]

    if len(morph_units) != len(gloss_units):
        raise ValueError(
            f"unaligned source analysis: {morph!r} ({len(morph_units)}) / "
            f"{gloss!r} ({len(gloss_units)})"
        )

    units: list[AnalysisUnit] = []
    for index, (form_unit, gloss_unit) in enumerate(zip(morph_units, gloss_units)):
        separator = morph_separators[index] if index < len(morph_separators) else ""
        if gloss_unit.casefold() == "red":
            role = "reduplicant"
        elif separator == "=":
            role = "infix"
        else:
            role = "regular"
        units.append(
            AnalysisUnit(
                form=form_unit,
                gloss=gloss_unit,
                role=role,
                boundary_after=separator.strip(),
            )
        )
    return units


def edit_distance(left: str, right: str) -> int:
    """Small deterministic Levenshtein implementation for gap inference."""

    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, 1):
        current = [row]
        for column, right_char in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def insertion_hosts(units: list[AnalysisUnit]) -> dict[int, int]:
    """Map every equals-linked unit to the regular unit that hosts it."""

    hosts: dict[int, int] = {}
    for index, unit in enumerate(units):
        if unit.boundary_after != "=":
            continue
        host_index = index + 1
        while host_index < len(units) and units[host_index].boundary_after == "=":
            host_index += 1
        if host_index >= len(units):
            raise ValueError("source analysis ends with an unattached '=' unit")
        hosts[index] = host_index
    return hosts


def infer_infix_positions(
    surface: str,
    units: list[AnalysisUnit],
    fixed_positions: dict[int, int] | None = None,
) -> tuple[dict[int, int], int]:
    """Infer equals-linked insertion gaps from the printed surface.

    Both infixes and equals-linked reduplicants participate in the alignment,
    because the latter can interrupt the lexical host in the printed word.
    Only infix positions are later rendered as angle brackets and M-tier root
    gaps. Positions are offsets in each host citation form. A caller may pin
    public, source-reviewed infix positions with ``fixed_positions``. Ties are
    resolved by source order and then the smallest position tuple.
    """

    hosts = insertion_hosts(units)
    inserted_indexes = list(hosts)
    fixed_positions = fixed_positions or {}
    unknown_indexes = [
        index for index in inserted_indexes if index not in fixed_positions
    ]
    target = normalized_letters(surface)

    candidates: list[tuple[int, tuple[int, ...], dict[int, int]]] = []

    def render(positions: dict[int, int]) -> str:
        insertions: dict[int, dict[int, list[str]]] = {}
        for inserted_index, host_index in hosts.items():
            position = positions[inserted_index]
            insertions.setdefault(host_index, {}).setdefault(position, []).append(
                units[inserted_index].form
            )

        rendered: list[str] = []
        for index, unit in enumerate(units):
            if index in hosts:
                continue
            by_position = insertions.get(index, {})
            for position in range(len(unit.form) + 1):
                rendered.extend(by_position.get(position, []))
                if position < len(unit.form):
                    rendered.append(unit.form[position])
        return "".join(rendered)

    def search(offset: int, positions: dict[int, int], prefix: tuple[int, ...]) -> None:
        if offset == len(unknown_indexes):
            candidate = normalized_letters(render(positions))
            candidates.append(
                (edit_distance(candidate, target), prefix, dict(positions))
            )
            return
        inserted_index = unknown_indexes[offset]
        host = units[hosts[inserted_index]].form
        for position in range(len(host) + 1):
            positions[inserted_index] = position
            search(offset + 1, positions, prefix + (position,))
        positions.pop(inserted_index, None)

    search(0, dict(fixed_positions), ())
    score, _prefix, positions = min(candidates, key=lambda item: (item[0], item[1]))
    return positions, score


def insert_markers(
    host: str, infixes: list[str], positions: list[int]
) -> tuple[str, str]:
    """Return W-level angle notation and M-level gap notation."""

    by_position: dict[int, list[str]] = {}
    for infix, position in zip(infixes, positions):
        by_position.setdefault(position, []).append(infix)

    word_parts: list[str] = []
    root_parts: list[str] = []
    for position in range(len(host) + 1):
        if position in by_position:
            root_parts.append("-")
            word_parts.extend(f"<{infix}>" for infix in by_position[position])
        if position < len(host):
            word_parts.append(host[position])
            root_parts.append(host[position])
    return "".join(word_parts), "".join(root_parts)


def canonical_word(
    units: list[AnalysisUnit],
    host_markers: dict[int, tuple[str, str]],
) -> tuple[str, str, list[str]]:
    """Build canonical W FORM, W gloss, and M forms from aligned units."""

    rendered_forms: list[str] = []
    rendered_glosses: list[str] = []
    m_forms: list[str] = []
    pending_infixes: list[AnalysisUnit] = []

    for index, unit in enumerate(units):
        if unit.role == "infix":
            pending_infixes.append(unit)
            m_forms.append(f"-{unit.form}-")
            continue

        if index in host_markers:
            word_form, root_form = host_markers[index]
        else:
            word_form, root_form = unit.form, unit.form

        gloss = unit.gloss
        if pending_infixes and index in host_markers:
            gloss += "".join(f"<{item.gloss}>" for item in pending_infixes)
        rendered_forms.append(word_form)
        rendered_glosses.append(gloss)
        m_forms.append(root_form)
        if pending_infixes and index in host_markers:
            pending_infixes.clear()

    if pending_infixes:
        raise ValueError("source analysis ends with an unattached infix")

    non_infix_units = [unit for unit in units if unit.role != "infix"]
    form = rendered_forms[0] if rendered_forms else ""
    gloss = rendered_glosses[0] if rendered_glosses else ""
    for index in range(1, len(rendered_forms)):
        previous = non_infix_units[index - 1]
        boundary = "~" if previous.role == "reduplicant" else "-"
        form += boundary + rendered_forms[index]
        gloss += boundary + rendered_glosses[index]
    return form, gloss.rstrip("-~"), m_forms
