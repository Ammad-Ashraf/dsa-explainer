"""The local API: jobs, events, lessons, saved plans and settings.

The pipeline is replaced by fakes that report events and write a small lesson
folder, so these tests need no API key and render nothing.
"""

import json
import time

import pytest
from dsa_explainer import config, pipeline, store
from dsa_explainer.api import create_app
from fastapi.testclient import TestClient

from .helpers import load


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    for name in ("DEFAULT_QUALITY", "VOICE", "VOICE_ENGINE", "VOICE_SPEED", "RENDER_WORKERS"):  # restored after
        monkeypatch.setattr(config, name, getattr(config, name))
    return tmp_path


@pytest.fixture
def client(home):
    with TestClient(create_app()) as c:
        yield c


def fake_finish(lesson, rep, version=1, folder=None, extra=None):
    """What pipeline._finish does, minus the voice and the drawing."""
    folder = folder or config.OUTPUT_DIR / store.new_id(lesson.title)
    folder.mkdir(parents=True, exist_ok=True)
    for stage in ("verify", "voice", "draw", "join"):
        rep.stage(stage, "running")
        rep.stage(stage, "done")
    rep.emit("clip", index=0, total=1, name="intro", key="0" * 20, seconds=3.0, cached=False)
    (folder / f"lesson_v{version}.mp4").write_bytes(b"\x00" * 2048)
    info = {"source": "test", "quality": "draft", "seconds": 3.0, "clips": 1, "rendered": ["intro"], "reused": 0,
            "chapters": [{"name": "intro", "kind": "intro", "start": 0, "seconds": 3.0}], "checks": 5,
            "rejected": [], **(extra or {})}
    store.save(folder, lesson, version, info)
    return {"lesson_id": folder.name, "version": version, "changed": (extra or {}).get("changed", [])}


def wait(client, job_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "failed", "cancelled"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_health_and_catalog(client):
    health = client.get("/api/health").json()
    assert health["ok"] and "llm" in health and "voice" in health
    catalog = client.get("/api/catalog").json()
    names = {a["id"] for a in catalog["algorithms"]}
    assert {"stack", "queue", "linked_list", "bst", "bfs", "quick_sort", "dijkstra"} <= names
    assert set(catalog["categories"]) >= {a["category"] for a in catalog["algorithms"]}
    assert all(a["complexity"] and a["summary"] and a["presets"] for a in catalog["algorithms"])


def test_saved_plans_are_listed_with_checked_quiz_answers(client):
    plans = client.get("/api/plans").json()
    assert {p["id"] for p in plans} >= {"stack", "bfs"}
    stack = client.get("/api/plans/stack").json()
    assert stack["verified"]["ok"]
    for q in stack["quiz"]:
        assert 0 <= q["answer"] < len(q["options"])
    assert client.get("/api/plans/nope").status_code == 404


def test_quiz_options_come_with_the_mistake_that_gives_them(client):
    """Saved questions carry no reasons; the API simulates the mistakes, and never explains the right answer."""
    explained = 0
    for plan in ("min_heap", "queue", "stack"):
        for q in client.get(f"/api/plans/{plan}").json()["quiz"]:
            assert str(q["answer"]) not in q["why_wrong"]
            explained += len(q["why_wrong"])
    assert explained > 0


def test_render_saved_plan_job_streams_events_and_records_the_lesson(client, monkeypatch):
    def from_file(path, quality, rep):
        rep.stage("plan", "skipped")
        return fake_finish(load(path.stem), rep, extra={"source": f"saved:{path.stem}"})

    monkeypatch.setattr(pipeline, "from_file", from_file)
    job = client.post("/api/plans/stack/render", json={"quality": "draft"}).json()
    assert job["status"] in ("queued", "running")

    with client.stream("GET", f"/api/jobs/{job['id']}/events") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        types = [line.split(": ", 1)[1] for line in response.iter_lines() if line.startswith("event: ")]
    assert types[-1] == "end"
    assert "clip" in types and "stage" in types

    done = wait(client, job["id"])
    assert done["status"] == "done" and done["stages"]["join"]["status"] == "done"
    lesson_id = done["result"]["lesson_id"]

    listed = client.get("/api/lessons").json()
    assert [item["id"] for item in listed] == [lesson_id]
    detail = client.get(f"/api/lessons/{lesson_id}").json()
    assert detail["version"] == 1 and detail["video_url"].endswith("/videos/1")
    assert detail["version_info"]["chapters"][0]["name"] == "intro"
    assert detail["scenes"][0]["kind"] == "intro" and detail["verified"]["ok"]

    video = client.get(detail["video_url"], headers={"Range": "bytes=0-99"})
    assert video.status_code == 206 and len(video.content) == 100


def test_events_can_be_resumed_after_an_id(client, monkeypatch):
    monkeypatch.setattr(pipeline, "from_file", lambda path, quality, rep: fake_finish(load("queue"), rep))
    job_id = client.post("/api/plans/queue/render").json()["id"]
    wait(client, job_id)
    every = client.get(f"/api/jobs/{job_id}").json()["event_log"]
    with client.stream("GET", f"/api/jobs/{job_id}/events", headers={"Last-Event-ID": "3"}) as response:
        ids = [int(line[4:]) for line in response.iter_lines() if line.startswith("id: ")]
    assert ids == [e["seq"] for e in every[4:]]


def test_failed_job_reports_the_error(client, monkeypatch):
    def broken(path, quality, rep):
        rep.stage("verify", "running")
        raise RuntimeError("the drawing broke")

    monkeypatch.setattr(pipeline, "from_file", broken)
    job = wait(client, client.post("/api/plans/bst/render").json()["id"])
    assert job["status"] == "failed" and "drawing broke" in job["error"]
    assert job["stages"]["verify"]["status"] == "failed"


def test_cancel_stops_a_running_job(client, monkeypatch):
    def slow(path, quality, rep):
        for _ in range(200):
            rep("working", 0.5)
            time.sleep(0.02)
        return {}

    monkeypatch.setattr(pipeline, "from_file", slow)
    job_id = client.post("/api/plans/stack/render").json()["id"]
    time.sleep(0.1)
    client.post(f"/api/jobs/{job_id}/cancel")
    assert wait(client, job_id)["status"] == "cancelled"


def test_new_lesson_needs_a_language_model(client, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    response = client.post("/api/lessons", json={"topic": "how does a stack work"})
    assert response.status_code == 400 and "API key" in response.json()["detail"]


def test_revision_creates_version_two(client, monkeypatch):
    monkeypatch.setattr(pipeline, "from_file", lambda path, quality, rep: fake_finish(load("stack"), rep))
    lesson_id = wait(client, client.post("/api/plans/stack/render").json()["id"])["result"]["lesson_id"]

    def revise_lesson(folder, version, request, quality, rep):
        return fake_finish(load("stack"), rep, version=version + 1, folder=folder,
                           extra={"request": request, "changed": ["step 2"]})

    monkeypatch.setattr(pipeline, "revise_lesson", revise_lesson)
    monkeypatch.setattr(config, "LLM_API_KEY", "")  # a speed change needs no language model
    started = client.post(f"/api/lessons/{lesson_id}/revisions", json={"request": "slow down step 2"}).json()
    job = wait(client, started["id"])
    assert job["status"] == "done" and job["result"]["version"] == 2
    detail = client.get(f"/api/lessons/{lesson_id}").json()
    assert [v["version"] for v in detail["versions"]] == [1, 2] and detail["version_info"]["changed"] == ["step 2"]
    assert client.get(f"/api/lessons/{lesson_id}?version=1").json()["version"] == 1

    rewrite = client.post(f"/api/lessons/{lesson_id}/revisions", json={"request": "explain step 2 for a beginner"})
    assert rewrite.status_code == 400


def test_lessons_are_protected_from_path_tricks(client):
    assert client.get("/api/lessons/..%2F..%2Fetc").status_code == 404
    assert client.get("/api/lessons/not-an-id").status_code == 404
    assert client.get("/api/clips/..%2F..%2Fsecret").status_code == 404
    plain = client.get("/api/clips/../../secret")  # normalised to /secret: the web app's page, never a file
    assert plain.status_code == 404 or plain.headers["content-type"].startswith("text/html")
    assert client.delete("/api/lessons/20260101-000000-missing").status_code == 404


def test_old_lesson_folders_without_meta_are_listed(client):
    folder = config.OUTPUT_DIR / "20261105-155231-breadth-first-search"
    folder.mkdir(parents=True)
    (folder / "lesson.json").write_text(load("bfs").model_dump_json(), encoding="utf-8")
    (folder / "lesson_v1.mp4").write_bytes(b"\x00")
    listed = client.get("/api/lessons").json()
    assert listed[0]["id"] == folder.name and listed[0]["versions"] == 1
    assert client.get(f"/api/lessons/{folder.name}").json()["version"] == 1
    assert client.delete(f"/api/lessons/{folder.name}").status_code == 204
    assert not folder.exists()


def test_settings_are_validated_and_saved(client, home):
    assert client.put("/api/settings", json={"default_quality": "ultra"}).status_code == 400
    assert client.put("/api/settings", json={"surprise": 1}).status_code == 400
    saved = client.put("/api/settings", json={"default_quality": "standard"}).json()
    assert saved["preferences"]["default_quality"] == "standard"
    assert json.loads((home / "settings.json").read_text())["preferences"]["default_quality"] == "standard"
