from typing import Any

from src.ai.bedrock_client import BedrockAiClient, _episode_from_text


def test_episode_parser_enforces_requested_target_minutes() -> None:
    text = """```json
    {
      "title": "Demo",
      "target_minutes": 1.2,
      "slides": [{
        "index": 1,
        "title": "Intro",
        "bullets": [],
        "narration": "Hello",
        "duration_seconds": 10
      }]
    }
    ```"""

    episode = _episode_from_text(text, 1)

    assert episode.target_minutes == 1
    assert sum(slide.duration_seconds for slide in episode.slides) == 60


def test_episode_parser_distributes_requested_duration_across_slides() -> None:
    text = """{
      "title": "Demo",
      "target_minutes": 1,
      "slides": [
        {"index": 1, "title": "One", "narration": "One", "duration_seconds": 10},
        {"index": 2, "title": "Two", "narration": "Two", "duration_seconds": 20}
      ]
    }"""

    episode = _episode_from_text(text, 2)

    assert [slide.duration_seconds for slide in episode.slides] == [40, 80]


class FakeBedrock:
    def __init__(self) -> None:
        self.calls = 0

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        self.calls += 1
        if self.calls == 1:
            text = '{"title":"Demo","target_minutes":1,"slides":[{"index":1,"title":"Intro","duration_seconds":10}]}'
        else:
            text = '{"title":"Demo","target_minutes":1,"slides":[{"index":1,"title":"Intro","duration_seconds":10,"dialogue":[{"speaker":"host","text":"Hello"},{"speaker":"guest","text":"Hi"}]}]}'
        return {"output": {"message": {"content": [{"text": text}]}}}


def test_invalid_episode_is_repaired_once() -> None:
    bedrock = FakeBedrock()
    client = BedrockAiClient.__new__(BedrockAiClient)
    client.client = bedrock
    client.model_id = "model"

    episode = client.generate_episode(AnyRepository(), "Demo", 1)

    assert bedrock.calls == 2
    assert episode.slides[0].dialogue[0].speaker == "host"


class AnyRepository:
    name = "demo"

    @staticmethod
    def model_dump_json(indent: int) -> str:
        del indent
        return "{}"
