from pathlib import Path

from src.ai.fake_client import FakeAiClient
from src.application.build_video import BuildVideo
from src.audio.fake_polly_client import FakeTtsClient


def test_fake_prepare_creates_all_intermediate_artifacts(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "README.md").write_text("# Demo", encoding="utf-8")
    episode, artifacts = BuildVideo(FakeAiClient(), FakeTtsClient()).prepare(
        repository, "Demo", 1, tmp_path / "dist", commit_sha="abc123"
    )
    assert artifacts.episode_json.exists()
    assert artifacts.script_markdown.exists()
    assert artifacts.srt.exists() and artifacts.vtt.exists()
    assert len(artifacts.audio_files) == 7
    assert episode.source_commit == "abc123"
    assert episode.source_repository == "repository"
    assert episode.source_paths == ["README.md"]
    assert any(slide.visual is not None for slide in episode.slides)
