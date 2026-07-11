import math
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from src.audio.polly_client import TtsClient
from src.domain.episode import Episode


class AudioRenderer:
    def __init__(self, client: TtsClient) -> None:
        self.client = client

    def render(
        self,
        episode: Episode,
        output_dir: Path,
        progress: Callable[[int, int], None] | None = None,
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []
        for slide in episode.slides:
            output = output_dir / f"{slide.index:03}.mp3"
            if not slide.dialogue:
                files.append(
                    self.client.synthesize(
                        slide.narration or "", output, slide.duration_seconds
                    )
                )
                if progress:
                    progress(len(files), len(episode.slides))
                continue

            parts_dir = output_dir / f".{slide.index:03}-parts"
            parts_dir.mkdir(parents=True, exist_ok=True)
            parts = [
                self.client.synthesize(
                    turn.text, parts_dir / f"{index:03}.mp3", voice_id=turn.speaker
                )
                for index, turn in enumerate(slide.dialogue, 1)
            ]
            self._concatenate(parts, output)
            shutil.rmtree(parts_dir)
            files.append(output)
            if progress:
                progress(len(files), len(episode.slides))
        return files

    @staticmethod
    def _concatenate(parts: list[Path], output: Path) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to concatenate dialogue audio")
        silence = parts[0].parent / "silence.mp3"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                "0.4",
                "-q:a",
                "9",
                str(silence),
            ],
            check=True,
            capture_output=True,
        )
        sequence: list[Path] = []
        for part in parts:
            if sequence:
                sequence.append(silence)
            sequence.append(part)
        # A short tail prevents scene changes from landing on the final phoneme.
        sequence.extend([silence, silence])
        concat_file = parts[0].parent / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{part.resolve().as_posix()}'" for part in sequence)
            + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(output),
            ],
            check=True,
            capture_output=True,
        )


def episode_with_audio_durations(episode: Episode, audio_files: list[Path]) -> Episode:
    if len(episode.slides) != len(audio_files):
        raise ValueError("Expected one audio file per slide")
    slides = [
        slide.model_copy(
            update={"duration_seconds": max(1, math.ceil(_audio_duration(audio)))}
        )
        for slide, audio in zip(episode.slides, audio_files, strict=True)
    ]
    return episode.model_copy(update={"slides": slides})


def _audio_duration(audio: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is required to measure narration audio")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())
