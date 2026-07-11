import json
import shlex
import shutil
import subprocess
from pathlib import Path

from src.audio.renderer import episode_with_audio_durations
from src.domain.episode import Episode


class RemotionRenderer:
    """Render an episode with the React composition in ``remotion/``."""

    def __init__(self, command: str = "npx remotion") -> None:
        self.command = shlex.split(command)

    def render(self, episode: Episode, audio_files: list[Path], output_path: Path) -> Path:
        if len(episode.slides) != len(audio_files):
            raise ValueError(
                f"Expected matching slides and audio, got {len(episode.slides)} and {len(audio_files)}"
            )
        episode = episode_with_audio_durations(episode, audio_files)
        executable = self.command[0]
        if shutil.which(executable) is None:
            raise RuntimeError(
                f"Remotion command not found: {executable}. Install the npm dependencies."
            )

        project_dir = Path(__file__).resolve().parents[2] / "remotion"
        if not (project_dir / "node_modules").exists():
            raise RuntimeError("Remotion dependencies are missing. Run `npm install` in remotion/.")

        render_dir = output_path.parent / ".remotion"
        public_dir = render_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        audio_names: list[str] = []
        for index, source in enumerate(audio_files, 1):
            name = f"audio-{index:03}{source.suffix.lower()}"
            shutil.copy2(source, public_dir / name)
            audio_names.append(name)

        props_path = render_dir / "props.json"
        props_path.write_text(
            json.dumps({"episode": episode.model_dump(), "audioFiles": audio_names}),
            encoding="utf-8",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            *self.command,
            "render",
            "src/index.ts",
            "Repodcast",
            output_path.resolve().as_posix(),
            f"--props={props_path.resolve().as_posix()}",
            f"--public-dir={public_dir.resolve().as_posix()}",
        ]
        try:
            subprocess.run(command, cwd=project_dir, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            details = (error.stderr or error.stdout or str(error)).strip()
            raise RuntimeError(f"Remotion render failed: {details}") from error
        return output_path
