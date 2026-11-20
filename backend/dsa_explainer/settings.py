"""Choices made in the app, kept in HOME/settings.json and applied over config.

Only known keys are stored; unknown keys in the file are ignored. The file stays
on this machine (it is outside git, and HOME is never served over HTTP).
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

from . import config

QUALITIES = ("draft", "standard", "high")

# key -> (config attribute, type, check)
PREFERENCES: dict[str, tuple[str, type, Any]] = {
    "default_quality": ("DEFAULT_QUALITY", str, lambda v: v in QUALITIES),
    "voice": ("KOKORO_VOICE", str, lambda v: 0 < len(v) <= 40),
    "render_workers": ("RENDER_WORKERS", int, lambda v: 1 <= v <= 16),
}

_lock = threading.Lock()


class SettingsError(ValueError):
    pass


def _read() -> dict:
    try:
        data = json.loads(config.SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(data: dict) -> None:
    config.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)  # private to this user where the OS supports it
    except OSError:
        pass
    tmp.replace(config.SETTINGS_FILE)


def raw() -> dict:
    """The whole settings file (other modules keep their own sections in it)."""
    with _lock:
        return _read()


def update_section(name: str, value: Any) -> None:
    with _lock:
        data = _read()
        data[name] = value
        _write(data)


def preferences() -> dict:
    """The effective preferences: stored choices, or the config defaults."""
    return {key: getattr(config, attr) for key, (attr, _, _) in PREFERENCES.items()}


def set_preferences(changes: dict) -> dict:
    clean = {}
    for key, value in changes.items():
        if key not in PREFERENCES:
            raise SettingsError(f"unknown setting '{key}'")
        _, kind, ok = PREFERENCES[key]
        try:
            value = kind(value)
        except (TypeError, ValueError) as exc:
            raise SettingsError(f"{key} must be a {kind.__name__}") from exc
        if not ok(value):
            raise SettingsError(f"{value!r} is not a valid {key}")
        clean[key] = value
    with _lock:
        data = _read()
        data.setdefault("preferences", {}).update(clean)
        _write(data)
    apply()
    return preferences()


def apply() -> None:
    """Copy stored preferences onto config, where the pipeline reads them."""
    stored = raw().get("preferences") or {}
    for key, (attr, kind, ok) in PREFERENCES.items():
        if key in stored:
            try:
                value = kind(stored[key])
            except (TypeError, ValueError):
                continue
            if ok(value):
                setattr(config, attr, value)
