from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "rules" / "price_source_manifest.json"


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def allowed_sources(manifest: dict | None = None) -> list[dict]:
    manifest = manifest or load_manifest()
    return [s for s in manifest["sources"] if s.get("allowed")]


def expected_allowed_files(manifest: dict | None = None) -> set[str]:
    return {s["file"] for s in allowed_sources(manifest)}


def preflight_missing_library_files(library_files: Iterable[str], manifest: dict | None = None) -> set[str]:
    """Allowed manifest files that are physically missing from /работа."""
    return expected_allowed_files(manifest) - set(library_files)


def preflight_unsynced_files(synced_index_files: Iterable[str], manifest: dict | None = None) -> set[str]:
    """Allowed manifest files missing from the complete Airtable/raw search index."""
    return expected_allowed_files(manifest) - set(synced_index_files)


def assert_ready_for_matching(
    library_files: Iterable[str],
    synced_index_files: Iterable[str],
    manifest: dict | None = None,
) -> None:
    """Block matching when the source universe is incomplete.

    This deliberately treats Library semantic search as a discovery helper only.
    Matching is allowed only after every allowed source in the deterministic manifest
    is present in Library and in the synchronized search index.
    """
    manifest = manifest or load_manifest()
    missing_library = sorted(preflight_missing_library_files(library_files, manifest))
    missing_index = sorted(preflight_unsynced_files(synced_index_files, manifest))
    problems: list[str] = []
    if missing_library:
        problems.append("missing from /работа: " + ", ".join(missing_library))
    if missing_index:
        problems.append("missing from synchronized index: " + ", ".join(missing_index))
    if problems:
        raise RuntimeError("Price-source preflight failed; matching is forbidden: " + "; ".join(problems))


def source_for_file(filename: str, manifest: dict | None = None) -> dict | None:
    manifest = manifest or load_manifest()
    for source in manifest["sources"]:
        if source["file"].casefold() == filename.casefold():
            return source
    return None
