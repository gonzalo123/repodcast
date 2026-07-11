from pathlib import Path

import pytest

from src.domain.episode import Episode
from src.domain.slide import Slide
from src.video.remotion import RemotionRenderer


def test_rejects_mismatched_audio_count(tmp_path: Path) -> None:
    episode = Episode(
        title="Demo",
        target_minutes=1,
        slides=[Slide(index=1, title="Intro", narration="Hello", duration_seconds=5)],
    )

    with pytest.raises(ValueError, match="matching slides and audio"):
        RemotionRenderer().render(episode, [], tmp_path / "video.mp4")
