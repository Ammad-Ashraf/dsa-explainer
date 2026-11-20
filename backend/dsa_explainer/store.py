"""The lessons made on this machine: one folder per lesson in OUTPUT_DIR.

    <id>/lesson.json         the latest verified plan
    <id>/lesson_v<n>.json    the plan of each version
    <id>/lesson_v<n>.mp4     the video of each version
    <id>/lesson_v<n>.vtt     its captions (WebVTT)
    <id>/meta.json           title, versions, timings, verification summary

Folders made before meta.json existed are still listed, from their files.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from . import config
from .core.lesson import Lesson

ID = re.compile(r"^[0-9]{8}-[0-9]{6}-[a-z0-9-]{1,60}$")
_VIDEO = re.compile(r"^lesson_v(\d+)\.mp4$")


class NotFound(LookupError):
    pass


def folder(lesson_id: str) -> Path:
    if not ID.match(lesson_id):
        raise NotFound(f"no lesson '{lesson_id}'")
    path = config.OUTPUT_DIR / lesson_id
    if not (path / "lesson.json").is_file():
        raise NotFound(f"no lesson '{lesson_id}'")
    return path


def new_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "lesson"
    base = f"{datetime.now():%Y%m%d-%H%M%S}-{slug}"
    lesson_id, n = base, 2
    while (config.OUTPUT_DIR / lesson_id).exists():
        lesson_id, n = f"{base}-{n}", n + 1
    return lesson_id


def read_meta(path: Path) -> dict:
    try:
        meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        meta = _meta_from_files(path)
    meta["id"] = path.name
    return meta


def _meta_from_files(path: Path) -> dict:
    lesson = Lesson.model_validate_json((path / "lesson.json").read_text(encoding="utf-8"))
    versions = sorted(int(m.group(1)) for f in path.iterdir() if (m := _VIDEO.match(f.name)))
    created = datetime.fromtimestamp((path / "lesson.json").stat().st_mtime).isoformat(timespec="seconds")
    return {
        "title": lesson.title, "topic": lesson.topic, "structure": lesson.structure, "level": lesson.level,
        "created": created, "source": "unknown",
        "versions": [{"version": v, "video": f"lesson_v{v}.mp4"} for v in versions],
    }


def save(path: Path, lesson: Lesson, version: int, info: dict) -> dict:
    """Record a new version (its plan and what the pipeline reported) and return the meta."""
    source = info.pop("source", "llm")
    if (path / "meta.json").exists() or (version > 1 and (path / "lesson.json").exists()):
        meta = read_meta(path)  # a later version (of a lesson that may predate meta.json)
    else:
        meta = {"title": lesson.title, "topic": lesson.topic, "structure": lesson.structure,
                "created": datetime.now().isoformat(timespec="seconds"), "source": source, "versions": []}
    meta.update({"title": lesson.title, "level": lesson.level})
    plan = lesson.model_dump_json(indent=2)
    (path / f"lesson_v{version}.json").write_text(plan, encoding="utf-8")
    (path / "lesson.json").write_text(plan, encoding="utf-8")
    meta["versions"] = [v for v in meta.get("versions", []) if v.get("version") != version]
    meta["versions"].append({"version": version, "video": f"lesson_v{version}.mp4",
                             "created": datetime.now().isoformat(timespec="seconds"), **info})
    meta["versions"].sort(key=lambda v: v["version"])
    meta.pop("id", None)
    (path / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["id"] = path.name
    return meta


def list_lessons() -> list[dict]:
    if not config.OUTPUT_DIR.is_dir():
        return []
    out = []
    for path in config.OUTPUT_DIR.iterdir():
        if ID.match(path.name) and (path / "lesson.json").is_file():
            try:
                out.append(summary(read_meta(path)))
            except (ValueError, OSError):
                continue  # a half-written or foreign folder: skip it
    return sorted(out, key=lambda m: m.get("created", ""), reverse=True)


def summary(meta: dict) -> dict:
    latest = meta["versions"][-1] if meta.get("versions") else {}
    return {
        "id": meta["id"], "title": meta.get("title", ""), "topic": meta.get("topic", ""),
        "structure": meta.get("structure", ""), "level": meta.get("level", ""), "created": meta.get("created", ""),
        "source": meta.get("source", "unknown"), "versions": len(meta.get("versions", [])),
        "latest_version": latest.get("version"), "seconds": latest.get("seconds"),
    }


def get(lesson_id: str) -> tuple[dict, Path]:
    path = folder(lesson_id)
    return read_meta(path), path


def lesson(lesson_id: str, version: int | None = None) -> Lesson:
    path = folder(lesson_id)
    file = path / f"lesson_v{version}.json" if version else path / "lesson.json"
    if not file.is_file():
        if version is None or not (path / "lesson.json").is_file():
            raise NotFound(f"lesson '{lesson_id}' has no version {version}")
        file = path / "lesson.json"  # folders from before per-version plans
    return Lesson.model_validate_json(file.read_text(encoding="utf-8"))


def video(lesson_id: str, version: int) -> Path:
    path = folder(lesson_id) / f"lesson_v{int(version)}.mp4"
    if not path.is_file():
        raise NotFound(f"lesson '{lesson_id}' has no video version {version}")
    return path


def captions(lesson_id: str, version: int) -> Path:
    path = folder(lesson_id) / f"lesson_v{int(version)}.vtt"
    if not path.is_file():
        raise NotFound(f"lesson '{lesson_id}' has no captions for version {version}")
    return path


def delete(lesson_id: str) -> None:
    path = folder(lesson_id)
    if path.resolve().parent != config.OUTPUT_DIR.resolve():
        raise NotFound(f"no lesson '{lesson_id}'")
    shutil.rmtree(path)


def clip(key: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{20}", key):
        raise NotFound("no such clip")
    path = config.CACHE_DIR / "clips" / f"{key}.mp4"
    if not path.is_file():
        raise NotFound("no such clip")
    return path
