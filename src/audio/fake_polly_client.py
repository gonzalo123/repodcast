import shutil
import subprocess
import wave
from pathlib import Path


class FakeTtsClient:
    def synthesize(
        self,
        text: str,
        output_path: Path,
        duration_seconds: int | None = None,
        voice_id: str | None = None,
    ) -> Path:
        del text
        del voice_id
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration = duration_seconds or 1
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg and output_path.suffix == ".mp3":
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=48000:cl=stereo",
                    "-t",
                    str(duration),
                    "-q:a",
                    "9",
                    output_path.as_posix(),
                ],
                check=True,
                capture_output=True,
            )
        else:
            output_path = output_path.with_suffix(".wav")
            with wave.open(str(output_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48_000)
                wav.writeframes(b"\0\0" * 48_000 * duration)
        return output_path
