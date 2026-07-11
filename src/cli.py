import json
from importlib.metadata import version
from pathlib import Path

import rich_click as click
from pydantic import ValidationError
from rich.console import Console

from src.ai.bedrock_client import BedrockAiClient
from src.ai.fake_client import FakeAiClient
from src.application.build_video import BuildVideo
from src.audio.fake_polly_client import FakeTtsClient
from src.audio.polly_client import PollyTtsClient
from src.audio.renderer import AudioRenderer
from src.domain.episode import Episode
from src.domain.repository import RepositorySummary
from src.repo.scanner import RepositoryScanner
from src.repo.source import RepositorySourceResolver, ResolvedRepository
from src.settings import Settings
from src.subtitles import cues_from_episode, write_srt, write_vtt
from src.ui import BuildDashboard
from src.video.remotion import RemotionRenderer

console = Console()
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True


def _read_model(
    path: Path, model: type[Episode] | type[RepositorySummary]
) -> Episode | RepositorySummary:
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, json.JSONDecodeError) as error:
        raise click.ClickException(f"Cannot read {path}: {error}") from error


def _write_model(model: Episode | RepositorySummary, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")


def _resolve_repository(
    source: str, ref: str | None, refresh: bool
) -> ResolvedRepository:
    try:
        resolved = RepositorySourceResolver().resolve(source, ref, refresh)
    except Exception as error:
        raise click.ClickException(f"Cannot resolve repository: {error}") from error
    if resolved.source_url:
        console.print(
            f"[green]✓[/green] GitHub repository: [cyan]{resolved.source_url.removesuffix('.git')}[/cyan]"
            f" at [cyan]{resolved.commit_sha[:12] if resolved.commit_sha else 'unknown'}[/cyan]"
        )
    return resolved


@click.group()
@click.version_option(version=version("repodcast"), prog_name="repodcast")
def cli() -> None:
    """Turn a source repository into a narrated technical video."""


@cli.command()
@click.argument("repository")
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("dist/repository.json"),
    show_default=True,
)
@click.option("--ref", help="Git branch or tag to clone.")
@click.option(
    "--refresh",
    is_flag=True,
    help="Discard and clone the cached GitHub checkout again.",
)
def analyze(repository: str, out: Path, ref: str | None, refresh: bool) -> None:
    """Scan REPOSITORY and write a deterministic summary."""
    settings = Settings()
    resolved = _resolve_repository(repository, ref, refresh)
    summary = RepositoryScanner(
        settings.max_file_bytes, settings.max_excerpt_chars
    ).scan(resolved.path)
    summary = summary.model_copy(
        update={
            "source_url": resolved.source_url,
            "requested_ref": resolved.requested_ref,
            "commit_sha": resolved.commit_sha,
        }
    )
    _write_model(summary, out)
    console.print(f"[green]✓[/green] Repository summary: [cyan]{out}[/cyan]")


@cli.command()
@click.argument(
    "repository_json", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("dist/episode.json"),
    show_default=True,
)
@click.option("--title")
@click.option("--minutes", type=click.IntRange(min=1), default=2, show_default=True)
@click.option(
    "--fake-ai", is_flag=True, help="Use deterministic offline content generation."
)
@click.option("--focus", help="Question or topic that should drive the episode.")
def episode(
    repository_json: Path,
    out: Path,
    title: str | None,
    minutes: int,
    fake_ai: bool,
    focus: str | None,
) -> None:
    """Generate an episode plan from REPOSITORY_JSON."""
    repository = _read_model(repository_json, RepositorySummary)
    assert isinstance(repository, RepositorySummary)
    client = FakeAiClient() if fake_ai else BedrockAiClient(Settings())
    result = client.generate_episode(repository, title, minutes, focus)
    result = result.model_copy(
        update={
            "source_commit": repository.commit_sha,
            "source_url": repository.source_url,
            "source_repository": repository.name,
            "source_paths": list(
                dict.fromkeys(
                    [
                        *(source.path for source in repository.interesting_files),
                        *repository.source_tree,
                    ]
                )
            )[:8],
        }
    )
    _write_model(result, out)
    console.print(f"[green]✓[/green] Episode plan: [cyan]{out}[/cyan]")


@cli.command("audio")
@click.argument(
    "episode_json", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("dist/audio"),
    show_default=True,
)
@click.option(
    "--fake-audio", is_flag=True, help="Generate silence instead of calling Polly."
)
def audio_command(episode_json: Path, out: Path, fake_audio: bool) -> None:
    """Generate one narration file per slide."""
    result = _read_model(episode_json, Episode)
    assert isinstance(result, Episode)
    client = FakeTtsClient() if fake_audio else PollyTtsClient(Settings())
    files = AudioRenderer(client).render(result, out)
    console.print(
        f"[green]✓[/green] Generated {len(files)} audio files in [cyan]{out}[/cyan]"
    )


@cli.command("subtitles")
@click.argument(
    "episode_json", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--out", type=click.Path(path_type=Path), default=Path("dist"), show_default=True
)
def subtitles_command(episode_json: Path, out: Path) -> None:
    """Generate SRT and WebVTT subtitles."""
    result = _read_model(episode_json, Episode)
    assert isinstance(result, Episode)
    cues = cues_from_episode(result)
    write_srt(cues, out / "subtitles.srt")
    write_vtt(cues, out / "subtitles.vtt")
    console.print(f"[green]✓[/green] Subtitle files: [cyan]{out}[/cyan]")


@cli.command()
@click.argument(
    "episode_json", type=click.Path(path_type=Path, exists=True, dir_okay=False)
)
@click.option(
    "--audio-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    required=True,
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("dist/video.mp4"),
    show_default=True,
)
def render(episode_json: Path, audio_dir: Path, out: Path) -> None:
    """Render an animated episode and narration into an MP4."""
    result = _read_model(episode_json, Episode)
    assert isinstance(result, Episode)
    settings = Settings()
    audio_files = sorted([*audio_dir.glob("*.mp3"), *audio_dir.glob("*.wav")])
    RemotionRenderer(settings.remotion_command).render(result, audio_files, out)
    console.print(f"[green]✓[/green] Video: [cyan]{out}[/cyan]")


@cli.command()
@click.argument("repository")
@click.option("--title")
@click.option("--focus", help="Question or topic that should drive the episode.")
@click.option("--minutes", type=click.IntRange(min=1), default=2, show_default=True)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("dist/repodcast.mp4"),
    show_default=True,
)
@click.option("--ref", help="Git branch or tag to clone.")
@click.option(
    "--refresh",
    is_flag=True,
    help="Discard and clone the cached GitHub checkout again.",
)
@click.option("--fake-ai", is_flag=True)
@click.option("--fake-audio", is_flag=True)
@click.option("--quiet", is_flag=True, help="Only print the generated video path.")
def build(
    repository: str,
    title: str | None,
    focus: str | None,
    minutes: int,
    out: Path,
    ref: str | None,
    refresh: bool,
    fake_ai: bool,
    fake_audio: bool,
    quiet: bool,
) -> None:
    """Run the complete repository-to-video pipeline."""
    settings = Settings()
    ai = FakeAiClient() if fake_ai else BedrockAiClient(settings)
    tts = FakeTtsClient() if fake_audio else PollyTtsClient(settings)
    dashboard = BuildDashboard(console, repository, minutes, focus, quiet)
    with dashboard:
        try:
            dashboard.start("resolve")
            resolved = RepositorySourceResolver().resolve(repository, ref, refresh)
            revision = resolved.commit_sha[:12] if resolved.commit_sha else "local"
            dashboard.complete("resolve", revision)
            dashboard.start("scan")
            use_case = BuildVideo(ai, tts, progress=dashboard.event)
            generated_episode, artifacts = use_case.prepare(
                resolved.path,
                title,
                minutes,
                out.parent,
                focus=focus,
                source_url=resolved.source_url,
                requested_ref=resolved.requested_ref,
                commit_sha=resolved.commit_sha,
            )
            dashboard.start("render")
            RemotionRenderer(settings.remotion_command).render(
                generated_episode, artifacts.audio_files, out
            )
            dashboard.complete("render")
        except Exception as error:
            dashboard.failure(error)
            raise click.ClickException("Build did not complete") from error

    duration = sum(slide.duration_seconds for slide in generated_episode.slides)
    dashboard.success(
        out,
        len(generated_episode.slides),
        duration,
        f"{artifacts.srt}, {artifacts.vtt}",
    )


if __name__ == "__main__":
    cli()
