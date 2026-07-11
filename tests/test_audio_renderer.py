from pathlib import Path

from src.audio.renderer import AudioRenderer
from src.domain.episode import Episode
from src.domain.slide import DialogueTurn, Slide


class RecordingTts:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def synthesize(
        self,
        text: str,
        output_path: Path,
        duration_seconds: int | None = None,
        voice_id: str | None = None,
    ) -> Path:
        self.calls.append((text, voice_id))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path


def test_dialogue_uses_speaker_voices(monkeypatch: object, tmp_path: Path) -> None:
    tts = RecordingTts()
    episode = Episode(
        title="Demo",
        target_minutes=1,
        slides=[
            Slide(
                index=1,
                title="Talk",
                dialogue=[
                    DialogueTurn(speaker="host", text="Hello"),
                    DialogueTurn(speaker="guest", text="Hi"),
                ],
                duration_seconds=10,
            ),
        ],
    )

    def concatenate(parts: list[Path], output: Path) -> None:
        output.write_bytes(b"joined")

    monkeypatch.setattr(AudioRenderer, "_concatenate", staticmethod(concatenate))  # type: ignore[attr-defined]
    files = AudioRenderer(tts).render(episode, tmp_path)

    assert tts.calls == [("Hello", "host"), ("Hi", "guest")]
    assert files[0].read_bytes() == b"joined"
