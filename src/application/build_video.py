from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.ai.bedrock_client import AiClient
from src.audio.polly_client import TtsClient
from src.audio.renderer import AudioRenderer, episode_with_audio_durations
from src.domain.episode import Episode
from src.repo.scanner import RepositoryScanner
from src.subtitles import cues_from_episode, write_srt, write_vtt


@dataclass(frozen=True)
class BuildArtifacts:
    repository_json: Path
    episode_json: Path
    script_markdown: Path
    audio_files: list[Path]
    srt: Path
    vtt: Path


@dataclass(frozen=True)
class BuildEvent:
    stage: str
    completed: int = 1
    total: int = 1
    detail: str | None = None


class BuildVideo:
    def __init__(
        self,
        ai: AiClient,
        tts: TtsClient,
        scanner: RepositoryScanner | None = None,
        progress: Callable[[BuildEvent], None] | None = None,
    ) -> None:
        self.ai = ai
        self.tts = tts
        self.scanner = scanner or RepositoryScanner()
        self.progress = progress or (lambda _: None)

    def prepare(
        self,
        repository_path: Path,
        title: str | None,
        minutes: int,
        work_dir: Path,
        focus: str | None = None,
        source_url: str | None = None,
        requested_ref: str | None = None,
        commit_sha: str | None = None,
    ) -> tuple[Episode, BuildArtifacts]:
        work_dir.mkdir(parents=True, exist_ok=True)
        repository = self.scanner.scan(repository_path).model_copy(
            update={
                "source_url": source_url,
                "requested_ref": requested_ref,
                "commit_sha": commit_sha,
            }
        )
        self.progress(BuildEvent("scan", detail=f"{len(repository.source_tree)} files"))
        repository_json = work_dir / "repository.json"
        repository_json.write_text(
            repository.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        self.progress(BuildEvent("episode", completed=0))
        episode = self.ai.generate_episode(repository, title, minutes, focus)
        episode = episode.model_copy(update={"source_commit": commit_sha})
        self.progress(BuildEvent("episode", detail=f"{len(episode.slides)} scenes"))
        self.progress(BuildEvent("audio", completed=0, total=len(episode.slides)))
        audio = AudioRenderer(self.tts).render(
            episode,
            work_dir / "audio",
            progress=lambda completed, total: self.progress(
                BuildEvent("audio", completed=completed, total=total)
            ),
        )
        episode = episode_with_audio_durations(episode, audio)
        episode_json = work_dir / "episode.json"
        episode_json.write_text(
            episode.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        script = work_dir / "script.md"
        script.write_text(
            "\n\n".join(f"## {s.title}\n\n{s.spoken_text}" for s in episode.slides)
            + "\n",
            encoding="utf-8",
        )
        self.progress(BuildEvent("subtitles", completed=0))
        cues = cues_from_episode(episode)
        srt = write_srt(cues, work_dir / "subtitles.srt")
        vtt = write_vtt(cues, work_dir / "subtitles.vtt")
        self.progress(BuildEvent("subtitles"))
        return episode, BuildArtifacts(
            repository_json, episode_json, script, audio, srt, vtt
        )
