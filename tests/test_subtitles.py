from pathlib import Path

from src.domain.episode import Episode
from src.domain.slide import DialogueTurn, Slide
from src.subtitles import cues_from_episode, write_srt, write_vtt


def test_subtitles_use_accumulated_slide_durations(tmp_path: Path) -> None:
    episode = Episode(
        title="Demo",
        target_minutes=1,
        slides=[
            Slide(index=1, title="One", narration="First", duration_seconds=18),
            Slide(index=2, title="Two", narration="Second", duration_seconds=24),
        ],
    )
    cues = cues_from_episode(episode)
    srt = write_srt(cues, tmp_path / "subtitles.srt")
    vtt = write_vtt(cues, tmp_path / "subtitles.vtt")
    assert "00:00:18,000 --> 00:00:42,000" in srt.read_text()
    assert vtt.read_text().startswith("WEBVTT")


def test_subtitles_include_dialogue_speakers() -> None:
    episode = Episode(
        title="Demo",
        target_minutes=1,
        slides=[
            Slide(
                index=1,
                title="Talk",
                dialogue=[
                    DialogueTurn(speaker="host", text="The idea is simple."),
                    DialogueTurn(speaker="guest", text="But does it work?"),
                ],
                duration_seconds=10,
            ),
        ],
    )

    assert cues_from_episode(episode)[0].text == (
        "host: The idea is simple.\nguest: But does it work?"
    )
