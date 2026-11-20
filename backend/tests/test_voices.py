"""Voice engines, the pronunciation lexicon, sentence timings and captions.

A fake engine (a tone whose length follows the text) stands in for Kokoro, so
these tests are fast and need no model files. One test speaks with the real
Kokoro when its files are downloaded.
"""

import wave

import numpy as np
import pytest
from dsa_explainer import config, settings
from dsa_explainer.api import create_app
from dsa_explainer.media import voices
from dsa_explainer.media.voices import lexicon
from dsa_explainer.media.voices.base import Engine, Voice
from fastapi.testclient import TestClient

from .helpers import load


class ToneEngine(Engine):
    """0.05 s of tone per letter: timings are predictable."""

    name, title, licence = "tone", "Test tone", "none"
    sample_rate = 8000

    def __init__(self):
        self.spoken = []

    def ready(self):
        return True

    def voices(self):
        return [Voice("low", "Low", "en-US"), Voice("high", "High", "en-US")]

    def synthesize(self, text, voice, speed=1.0):
        self.spoken.append(text)
        n = int(self.sample_rate * 0.05 * len(text) / speed)
        freq = 220 if voice == "low" else 440
        return (0.2 * np.sin(np.arange(n) * 2 * np.pi * freq / self.sample_rate)).astype(np.float32)


@pytest.fixture
def tone(tmp_path, monkeypatch):
    engine = ToneEngine()
    monkeypatch.setitem(voices.ENGINES, "tone", engine)
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    for name, value in (("VOICE_ENGINE", "tone"), ("VOICE", "low"), ("VOICE_SPEED", 1.0)):
        monkeypatch.setattr(config, name, value)
    return engine


# --- lexicon -------------------------------------------------------------------------------


@pytest.mark.parametrize("written, spoken", [
    ("BFS visits A first.", "B F S visits A first."),
    ("Sorting takes O(n log n) time, bubble sort O(n^2).",
     "Sorting takes O of n log n time, bubble sort O of n squared."),
    ("It runs in O(V + E).", "It runs in O of V plus E."),
    ("We dequeue 3 and enqueue 8.", "We dee-queue 3 and en-queue 8."),
    ("A deque has two ends.", "A deck has two ends."),
    ("Dijkstra's algorithm settles A.", "Dike-struh's algorithm settles A."),
    ("After pop() and push(7), the top is 7.", "After pop and push 7, the top is 7."),
    ("a[i] is compared with a[j + 1].", "a of i is compared with a of j + 1."),
    ("dist[B] -> 4, and C stays inf.", "dist of B to 4, and C stays infinity."),
    ("Check 2 <= 5 and 1 + 3 = 4.", "Check 2 at most 5 and 1 plus 3 equals 4."),
    ("A stack is LIFO; a queue is FIFO.", "A stack is lie-foe; a queue is fie-foe."),
    ("The BST root is 8.", "The B S T root is 8."),
])
def test_lexicon_reads_notation_and_terms_aloud(written, spoken):
    assert lexicon.speakable(written) == spoken


def test_lexicon_leaves_ordinary_words_alone():
    text = "The queue is empty, so the dequeued value was the last one. Subsequent values wait."
    assert lexicon.speakable(text) == text.replace("dequeued", "dee-queued")
    assert lexicon.speakable("BFSX and DFSs are not acronyms we know.") == "BFSX and DFSs are not acronyms we know."


# --- timings and captions ---------------------------------------------------------------------


def test_sentences_split_after_full_stops_but_not_inside_numbers():
    assert voices.sentences("Push 2.5 now. Is it on top? Yes!") == ["Push 2.5 now.", "Is it on top?", "Yes!"]


def test_speech_is_timed_by_sentence_and_cached(tone):
    text = "Push seven. The top is seven."
    speech = voices.speak(text)
    with wave.open(speech.path) as w:
        assert w.getframerate() == 8000
    first, second = speech.cues
    assert first[2] == "Push seven." and second[2] == "The top is seven."
    assert first[0] == 0 and first[1] == pytest.approx(0.05 * len("Push seven."), abs=0.01)
    assert second[0] == pytest.approx(first[1] + voices.SENTENCE_PAUSE, abs=0.01)
    assert second[1] == pytest.approx(speech.seconds, abs=0.01)
    calls = len(tone.spoken)
    assert voices.speak(text).path == speech.path and len(tone.spoken) == calls  # cached
    assert voices.speak(text, voice="high").path != speech.path  # the voice is part of the key


def test_the_engine_hears_the_lexicon_but_captions_keep_the_written_words(tone):
    speech = voices.speak("BFS uses a queue.")
    assert tone.spoken == ["B F S uses a queue."]
    assert speech.cues[0][2] == "BFS uses a queue."


def test_long_sentences_become_several_captions_in_order(tone):
    text = ("In the first pass, five swaps past one, four and two, and later eight swaps past three, "
            "so eight ends in its final place at the end of the array.")
    cues = voices.speak(text).cues
    assert len(cues) >= 2 and " ".join(c[2] for c in cues) == text
    assert all(len(c[2].split()) <= voices.CAPTION_WORDS for c in cues)
    for a, b in zip(cues, cues[1:]):
        assert a[0] < a[1] == pytest.approx(b[0], abs=0.002)


def test_webvtt_format():
    vtt = voices.captions_vtt([[0, 1.5, "Push seven."], [61.25, 3723.5, "Done --> next"]])
    assert vtt.startswith("WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.500\nPush seven.\n")
    assert "00:01:01.250 --> 01:02:03.500\nDone -> next" in vtt


def test_global_speed_multiplies_the_scene_speed(tone, monkeypatch):
    normal = voices.speak("A short sentence here.").seconds
    monkeypatch.setattr(config, "VOICE_SPEED", 1.25)
    assert voices.speak("A short sentence here.").seconds == pytest.approx(normal / 1.25, rel=0.02)


# --- settings and API ----------------------------------------------------------------------------


def test_settings_accept_known_engines_and_sane_speeds(tone):
    assert settings.set_preferences({"voice_engine": "tone", "voice": "high", "voice_speed": 1.1})["voice"] == "high"
    assert config.VOICE == "high" and config.VOICE_SPEED == 1.1
    for bad in ({"voice_engine": "nope"}, {"voice_speed": 3}):
        with pytest.raises(settings.SettingsError):
            settings.set_preferences(bad)


def test_api_lists_engines_and_previews_a_voice(tone, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    with TestClient(create_app()) as client:
        data = client.get("/api/voices").json()
        engine = next(e for e in data["engines"] if e["id"] == "tone")
        assert [v["id"] for v in engine["voices"]] == ["low", "high"] and engine["ready"]
        assert data["current"] == {"engine": "tone", "voice": "low", "speed": 1.0}
        reply = client.post("/api/voices/preview", json={"engine": "tone", "voice": "high", "speed": 1.0})
        assert reply.status_code == 200 and reply.headers["content-type"] == "audio/wav"
        assert reply.content[:4] == b"RIFF"
        assert client.post("/api/voices/preview", json={"engine": "tone", "voice": "nobody"}).status_code == 400
        assert client.post("/api/voices/preview", json={"engine": "tone", "speed": 9}).status_code == 422
        assert client.get("/api/health").json()["voice"] == {"ready": True, "engine": "tone", "voice": "low"}


def test_captions_are_served_for_a_lesson_version(tone, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    folder = config.OUTPUT_DIR / "20261120-120000-stack"
    folder.mkdir(parents=True)
    (folder / "lesson.json").write_text(load("stack").model_dump_json(), encoding="utf-8")
    (folder / "lesson_v1.vtt").write_text(voices.captions_vtt([[0, 1, "Hello."]]), encoding="utf-8")
    with TestClient(create_app()) as client:
        reply = client.get("/api/lessons/20261120-120000-stack/captions/1")
        assert reply.status_code == 200 and reply.text.startswith("WEBVTT")
        assert "text/vtt" in reply.headers["content-type"]
        assert client.get("/api/lessons/20261120-120000-stack/captions/2").status_code == 404


@pytest.mark.skipif(not config.KOKORO_MODEL.exists(), reason="voice model not downloaded")
def test_kokoro_speaks_with_sentence_timings(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    engine = voices.engine("kokoro")
    assert any(v.id == "af_heart" for v in engine.voices())
    speech = voices.speak("Push seven. The top is seven.", voice="af_heart", engine_name="kokoro")
    assert 1.0 < speech.seconds < 6.0 and len(speech.cues) == 2
    assert speech.cues[-1][1] == pytest.approx(speech.seconds, abs=0.05)
