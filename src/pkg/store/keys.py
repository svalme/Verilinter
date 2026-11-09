"""The tokens that decide whether a stored analysis result still applies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..rules.rule_selection import RuleSelection

ANALYZER_CACHE_VERSION = "2026-11-08-named-type-elements-have-no-declared-width"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selection_key(
    selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry_fingerprint: str | None = None,
    defines: list[str] | None = None,
) -> str:
    payload = {
        "analyzer_cache_version": ANALYZER_CACHE_VERSION,
        "enabled_codes": sorted(selection.enabled_codes) if selection and selection.enabled_codes else None,
        "enabled_categories": sorted(selection.enabled_categories)
        if selection and selection.enabled_categories
        else None,
        "enabled_profiles": sorted(selection.enabled_profiles) if selection and selection.enabled_profiles else None,
        # A cached per-file result was parsed with a specific set of `--include-dir`
        # search paths; changing them can change how `` `include ``/macro
        # resolution -- and therefore the parsed AST -- comes out for the same
        # file content, so this must be part of the cache key too.
        "include_dirs": include_dirs or None,
        # A cached per-file result was also resolved against a specific
        # corpus-wide set of package declarations (run_lint.py's `_scan_packages`
        # pre-pass) -- a package changing in a DIFFERENT file can change what a
        # package-qualified/wildcard-imported name resolves to for this file, so
        # this must be part of the key too even though the file's own content
        # didn't change. See `seed_cross_file_packages`.
        "package_registry_fingerprint": package_registry_fingerprint,
        # Preprocessor defines (-D) change macro expansion and conditional
        # compilation branches (`ifdef / `ifndef), so they must be part of the cache key.
        "defines": sorted(defines) if defines else None,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
