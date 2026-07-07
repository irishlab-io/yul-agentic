"""
DELIBERATELY VULNERABLE FEATURE FLAGS MODULE - FOR EDUCATIONAL PURPOSES ONLY

This module provides a simple feature flag system backed by a YAML file.
Flags can be toggled on or off per-feature and per-sub-feature.  When no
configuration file is supplied every feature is enabled by default.

Vulnerabilities demonstrated (intentional, for learning):
- CWE-502: Unsafe YAML deserialization via yaml.load() with full Loader
            (allows arbitrary Python object instantiation / code execution)
- CWE-284: Runtime feature-flag bypass exposed through a query parameter
- CWE-200: All flag state disclosed to unauthenticated callers via the API
- CWE-22:  Flag-file path accepted from an environment variable without
            any sanitisation (path traversal is possible)
"""

import os
from typing import Any, Dict, Optional

import yaml


# ---------------------------------------------------------------------------
# Default flag definitions – every feature enabled by default.
# These are used when no YAML file is present or the file cannot be parsed.
# ---------------------------------------------------------------------------
DEFAULT_FLAGS: Dict[str, Any] = {
    "authentication": {
        "enabled": True,
        "login": True,
        "register": True,
        "session": True,
    },
    "todos": {
        "enabled": True,
        "create": True,
        "read": True,
        "update": True,
        "delete": True,
        "sharing": True,
    },
    "admin": {
        "enabled": True,
        "panel": True,
        "command_execution": True,
    },
    "files": {
        "enabled": True,
        "upload": True,
        "download": True,
    },
    "api": {
        "enabled": True,
        "todos": True,
    },
    "search": {
        "enabled": True,
    },
    "utilities": {
        "enabled": True,
        "ssrf": True,
        "xxe": True,
    },
}

# Module-level flag store populated by load_flags().
_flags: Dict[str, Any] = {}


def load_flags(flags_file: Optional[str] = None) -> None:
    """
    Load feature flags from a YAML file into the module-level store.

    Resolution order:
    1. The ``flags_file`` argument (if provided).
    2. The ``FEATURE_FLAGS_FILE`` environment variable.
    3. ``feature_flags.yml`` in the current working directory.

    If the resolved file does not exist all flags default to *enabled*.

    Parameters:
    flags_file (Optional[str]): Explicit path to the YAML configuration file.

    CWE-22: The file path is used as-is; an attacker who controls the
    FEATURE_FLAGS_FILE environment variable can read arbitrary files.
    CWE-502: yaml.load() with Loader=yaml.Loader deserialises arbitrary
    Python objects, enabling remote code execution if the YAML is attacker-
    controlled.  Always use yaml.safe_load() in production code.
    """
    global _flags

    # CWE-22: Path accepted from env var without sanitisation or canonicalisation.
    if flags_file is None:
        flags_file = os.environ.get("FEATURE_FLAGS_FILE", "feature_flags.yml")

    # CWE-200: Printing the file path leaks filesystem information.
    print(f"[FeatureFlags] Loading flags from: {flags_file}")

    if os.path.exists(flags_file):
        try:
            with open(flags_file, "r") as fh:
                # VULNERABILITY: CWE-502 – yaml.load with the full Loader
                # allows execution of arbitrary Python code embedded in the
                # YAML file (e.g. !!python/object/apply:os.system ["cmd"]).
                # Replace with yaml.safe_load(fh) in a real application.
                loaded = yaml.load(fh, Loader=yaml.Loader)  # noqa: S506

            if loaded and isinstance(loaded, dict) and "features" in loaded:
                _flags = loaded["features"]
                # CWE-200: Leaking loaded flag names to stdout.
                print(
                    f"[FeatureFlags] Loaded {len(_flags)} feature(s): {list(_flags.keys())}"
                )
            else:
                print("[FeatureFlags] 'features' key missing – using defaults")
                _flags = dict(DEFAULT_FLAGS)
        except Exception as exc:
            # CWE-200: Exposing internal error details.
            print(
                f"[FeatureFlags] Failed to parse {flags_file}: {exc} – using defaults"
            )
            _flags = dict(DEFAULT_FLAGS)
    else:
        print("[FeatureFlags] Config file not found – all features enabled by default")
        _flags = dict(DEFAULT_FLAGS)


def is_enabled(feature: str, sub_feature: Optional[str] = None) -> bool:
    """
    Return ``True`` when *feature* (and optionally *sub_feature*) is enabled.

    Unknown features are treated as enabled so that the application degrades
    gracefully when a flag is not yet defined in the configuration file.

    Parameters:
    feature (str): Top-level feature key (e.g. ``"admin"``).
    sub_feature (Optional[str]): Sub-feature key (e.g. ``"command_execution"``).

    Returns:
    bool: ``True`` if the feature is enabled, ``False`` otherwise.
    """
    if not _flags:
        load_flags()

    feature_config = _flags.get(feature)

    # Feature not declared → enabled by default (fail-open).
    if feature_config is None:
        return True

    if isinstance(feature_config, bool):
        return feature_config

    if isinstance(feature_config, dict):
        # A disabled parent feature disables all its children too.
        if not feature_config.get("enabled", True):
            return False

        if sub_feature is not None:
            return bool(feature_config.get(sub_feature, True))

        return True

    return bool(feature_config)


def get_all_flags() -> Dict[str, Any]:
    """
    Return all feature flags and their current values.

    CWE-200: This function is intentionally called by an unauthenticated
    API endpoint (/api/features) that exposes the entire flag configuration
    to any caller.  Restrict this to administrators in production code.

    Returns:
    Dict[str, Any]: Shallow copy of the current flag store.
    """
    if not _flags:
        load_flags()
    return dict(_flags)


def set_flag(feature: str, value: bool, sub_feature: Optional[str] = None) -> None:
    """
    Override a feature flag value at runtime without authentication.

    CWE-284: No access control is enforced.  Any caller – including code
    that handles unauthenticated HTTP query parameters – can toggle any
    flag, potentially re-enabling disabled features.

    Parameters:
    feature (str): Top-level feature key.
    value (bool): ``True`` to enable, ``False`` to disable.
    sub_feature (Optional[str]): Sub-feature key to modify.
    """
    global _flags

    if not _flags:
        load_flags()

    if feature not in _flags:
        _flags[feature] = {}

    if sub_feature is not None:
        if not isinstance(_flags[feature], dict):
            _flags[feature] = {"enabled": bool(_flags[feature])}
        _flags[feature][sub_feature] = value
    else:
        if isinstance(_flags[feature], dict):
            _flags[feature]["enabled"] = value
        else:
            _flags[feature] = value


def reload_flags(flags_file: Optional[str] = None) -> None:
    """
    Reload feature flags from disk, discarding any runtime overrides.

    Useful for testing and for picking up configuration changes without
    restarting the application.

    Parameters:
    flags_file (Optional[str]): Path override passed directly to load_flags().
    """
    global _flags
    _flags = {}
    load_flags(flags_file)


# ---------------------------------------------------------------------------
# Eagerly load flags when this module is first imported.
# ---------------------------------------------------------------------------
load_flags()
