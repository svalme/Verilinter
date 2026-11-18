"""The tokens that decide whether a stored analysis result still applies."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from importlib import metadata
from pathlib import Path

from ..rules.rule_selection import RuleSelection

ANALYZER_CACHE_VERSION = "2026-11-12-instance-driver-events"

# The cache row that holds a file's module ports and instantiated modules carries this value in place of a
# package-registry fingerprint, which keeps it apart from the file's analysis result.
MODULE_PORT_SCAN_FINGERPRINT = "module_ports"
MODULE_PORT_SCAN_KEY_FRAGMENT = '"package_registry_fingerprint":"module_ports"'


@lru_cache(maxsize=1)
def pyslang_version() -> str:
    """The installed pyslang version; a different parser can change the tree a stored result came from."""
    try:
        return metadata.version("pyslang")
    except metadata.PackageNotFoundError:
        return "unknown"


@lru_cache(maxsize=1)
def analyzer_code_fingerprint() -> str:
    """A hash of Verilinter's own source (every `.py` file under `src/pkg`).

    A stored result is only valid for the code that produced it, so the key carries this alongside the
    hand-set `ANALYZER_CACHE_VERSION`: a change to a rule, handler or helper invalidates old rows without
    anyone having to remember to bump the token."""
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


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
        "analyzer_code": analyzer_code_fingerprint(),
        "pyslang": pyslang_version(),
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


def elaboration_keys(
    file_hashes: dict[str, str],
    header_dependencies: list[dict[str, str]],
    include_dirs: list[str] | None,
    defines: list[str] | None,
) -> tuple[str, str]:
    """The two tokens of an elaboration cache row, as (set id, input key).

    The set id names the file set: the paths, the ordered include directories and the defines. The input key is
    everything the record was built from: each file's content hash, the hash of every included header, and the
    analyzer and pyslang versions (a different slang or a changed Verilinter can change the widths). A change to
    any of them gives a different input key, so the stored record is not reused."""

    def normal(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    set_payload = {
        "paths": sorted(normal(path) for path in file_hashes),
        "include_dirs": include_dirs or None,
        "defines": sorted(defines) if defines else None,
    }
    input_payload = {
        "analyzer_cache_version": ANALYZER_CACHE_VERSION,
        "analyzer_code": analyzer_code_fingerprint(),
        "pyslang": pyslang_version(),
        "files": sorted((normal(path), digest) for path, digest in file_hashes.items()),
        "headers": sorted({(normal(dep["path"]), dep["hash"]) for dep in header_dependencies}),
    }

    def digest(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    return digest(set_payload), digest(input_payload)
