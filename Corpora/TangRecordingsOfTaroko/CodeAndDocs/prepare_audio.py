#!/usr/bin/env python3
"""Verify and convert the pinned Tang recordings to canonical WAV files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import wave
from pathlib import Path
from urllib.parse import quote

from make_xml import CORPUS_ROOT, MANIFEST, load_manifest


DEFAULT_OUTPUT = CORPUS_ROOT / "Audio" / "Truku"


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_wave(file_path: Path) -> dict[str, object]:
    with wave.open(str(file_path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        return {
            "codec": "pcm_s16le" if audio.getsampwidth() == 2 else "unknown",
            "sample_rate_hz": rate,
            "channels": audio.getnchannels(),
            "sample_width_bits": audio.getsampwidth() * 8,
            "compression": audio.getcomptype(),
            "frames": frames,
            "duration_seconds": frames / rate,
        }


def assert_format(
    file_path: Path, expected: dict[str, object], expected_frames: int | None = None
) -> dict[str, object]:
    actual = inspect_wave(file_path)
    for key in ("codec", "sample_rate_hz", "channels", "sample_width_bits"):
        if actual[key] != expected[key]:
            raise ValueError(
                f"{file_path.name}: expected {key}={expected[key]!r}, "
                f"found {actual[key]!r}"
            )
    if actual["compression"] != "NONE":
        raise ValueError(f"{file_path.name}: WAV compression is not PCM")
    if expected_frames is not None and actual["frames"] != expected_frames:
        raise ValueError(
            f"{file_path.name}: expected {expected_frames} frames, "
            f"found {actual['frames']}"
        )
    return actual


def assert_identity(
    file_path: Path, expected_bytes: int, expected_sha256: str
) -> None:
    actual_bytes = file_path.stat().st_size
    if actual_bytes != expected_bytes:
        raise ValueError(
            f"{file_path.name}: expected {expected_bytes} bytes, found {actual_bytes}"
        )
    actual_sha256 = sha256_file(file_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"{file_path.name}: expected SHA-256 {expected_sha256}, "
            f"found {actual_sha256}"
        )


def resolve_local_source(source_dir: Path, entry: dict[str, object]) -> Path:
    candidates = [
        source_dir / str(entry["hf_path"]),
        source_dir / str(entry["file"]),
        source_dir / "Truku" / str(entry["file"]),
    ]
    for candidate in dict.fromkeys(candidates):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"source audio not found for {entry['file']}")


def acquire_source(
    entry: dict[str, object], manifest: dict[str, object], destination: Path,
    source_dir: Path | None,
) -> None:
    if source_dir is not None:
        shutil.copyfile(resolve_local_source(source_dir, entry), destination)
        return

    source = manifest["source"]
    source_path = quote(str(entry["hf_path"]))
    url = (
        f"https://huggingface.co/datasets/{source['repo_id']}/resolve/"
        f"{source['revision']}/{source_path}"
    )
    subprocess.run(
        [
            "curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "5",
            "--retry-delay",
            "2",
            "--output",
            str(destination),
            url,
        ],
        check=True,
    )


def prepared_identity(entry: dict[str, object]) -> tuple[int, str, int] | None:
    keys = ("prepared_bytes", "prepared_sha256", "prepared_frames")
    if not all(entry.get(key) for key in keys):
        return None
    return int(entry["prepared_bytes"]), str(entry["prepared_sha256"]), int(
        entry["prepared_frames"]
    )


def assert_ffmpeg_version(expected: str) -> None:
    result = subprocess.run(
        ["ffmpeg", "-version"], check=True, capture_output=True, text=True
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    if not first_line.startswith(f"ffmpeg version {expected} "):
        raise RuntimeError(
            f"expected ffmpeg {expected}, found {first_line or 'unknown version'}"
        )


def verify_prepared(
    output_path: Path, entry: dict[str, object], manifest: dict[str, object]
) -> dict[str, object]:
    expected = prepared_identity(entry)
    if expected is None:
        raise ValueError(f"{entry['file']}: prepared identity is not pinned")
    expected_bytes, expected_sha256, expected_frames = expected
    assert_identity(output_path, expected_bytes, expected_sha256)
    return assert_format(
        output_path, manifest["prepared"]["format"], expected_frames
    )


def prepare_one(
    entry: dict[str, object], manifest: dict[str, object], output_dir: Path,
    source_dir: Path | None, bootstrap: bool,
) -> dict[str, object]:
    output_path = output_dir / str(entry["file"])
    source_tmp = output_dir / f".{entry['file']}.source.tmp"
    output_tmp = output_dir / f".{entry['file']}.prepared.tmp.wav"
    for temporary in (source_tmp, output_tmp):
        temporary.unlink(missing_ok=True)

    try:
        acquire_source(entry, manifest, source_tmp, source_dir)
        assert_identity(
            source_tmp, int(entry["source_bytes"]), str(entry["source_sha256"])
        )
        source_wave = assert_format(
            source_tmp,
            manifest["source"]["format"],
            int(entry["source_frames"]),
        )

        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source_tmp),
                *manifest["prepared"]["ffmpeg_args"],
                str(output_tmp),
            ],
            check=True,
        )
        prepared_wave = assert_format(output_tmp, manifest["prepared"]["format"])
        if abs(
            float(source_wave["duration_seconds"])
            - float(prepared_wave["duration_seconds"])
        ) > 0.001:
            raise ValueError(f"{entry['file']}: conversion changed duration")

        result = {
            "file": entry["file"],
            "prepared_bytes": output_tmp.stat().st_size,
            "prepared_sha256": sha256_file(output_tmp),
            "prepared_frames": prepared_wave["frames"],
            "prepared_duration_seconds": round(
                float(prepared_wave["duration_seconds"]), 6
            ),
        }
        expected = prepared_identity(entry)
        if expected is None and not bootstrap:
            raise ValueError(f"{entry['file']}: prepared identity is not pinned")
        if expected is not None:
            actual = (
                result["prepared_bytes"],
                result["prepared_sha256"],
                result["prepared_frames"],
            )
            if actual != expected:
                raise ValueError(
                    f"{entry['file']}: prepared output differs from manifest"
                )
        output_tmp.replace(output_path)
        return result
    finally:
        source_tmp.unlink(missing_ok=True)
        output_tmp.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.bootstrap and args.verify_only:
        raise SystemExit("--bootstrap and --verify-only cannot be combined")
    manifest = load_manifest(MANIFEST)
    entries = manifest["files"]
    known_names = {entry["file"] for entry in entries}
    unknown = set(args.only) - known_names
    if unknown:
        raise SystemExit(f"unknown --only values: {sorted(unknown)}")
    if args.only:
        entries = [entry for entry in entries if entry["file"] in args.only]

    if not args.verify_only:
        assert_ffmpeg_version(str(manifest["prepared"]["ffmpeg_version"]))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, entry in enumerate(entries, 1):
        output_path = args.output_dir / str(entry["file"])
        if args.verify_only:
            properties = verify_prepared(output_path, entry, manifest)
            result = {
                "file": entry["file"],
                "prepared_bytes": output_path.stat().st_size,
                "prepared_sha256": sha256_file(output_path),
                "prepared_frames": properties["frames"],
                "prepared_duration_seconds": round(
                    float(properties["duration_seconds"]), 6
                ),
            }
            action = "verified"
        elif output_path.is_file() and not args.rebuild and prepared_identity(entry):
            properties = verify_prepared(output_path, entry, manifest)
            result = {
                "file": entry["file"],
                "prepared_bytes": output_path.stat().st_size,
                "prepared_sha256": str(entry["prepared_sha256"]),
                "prepared_frames": properties["frames"],
                "prepared_duration_seconds": round(
                    float(properties["duration_seconds"]), 6
                ),
            }
            action = "verified"
        else:
            result = prepare_one(
                entry, manifest, args.output_dir, args.source_dir, args.bootstrap
            )
            action = "prepared"
        results.append(result)
        print(f"[{index}/{len(entries)}] {action} {entry['file']}", flush=True)

    report = {
        "source_revision": manifest["source"]["revision"],
        "files": results,
        "total_files": len(results),
        "total_seconds": round(
            sum(float(item["prepared_duration_seconds"]) for item in results), 6
        ),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        f"Prepared audio: {report['total_files']} files, "
        f"{report['total_seconds'] / 3600:.6f} hours."
    )


if __name__ == "__main__":
    main()
