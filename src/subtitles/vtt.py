from pathlib import Path

from src.domain.subtitle import SubtitleCue
from src.subtitles.srt import timestamp


def write_vtt(cues: list[SubtitleCue], output_path: Path) -> Path:
    blocks = [
        f"{cue.index}\n{timestamp(cue.start_seconds, '.')} --> {timestamp(cue.end_seconds, '.')}\n{cue.text}"
        for cue in cues
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("WEBVTT\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")
    return output_path
