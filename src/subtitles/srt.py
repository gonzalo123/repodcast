from pathlib import Path

from src.domain.episode import Episode
from src.domain.subtitle import SubtitleCue


def cues_from_episode(episode: Episode) -> list[SubtitleCue]:
    start = float(episode.intro_duration_seconds)
    cues = []
    for slide in episode.slides:
        end = start + slide.duration_seconds
        cues.append(
            SubtitleCue(
                index=slide.index, start_seconds=start, end_seconds=end, text=slide.spoken_text
            )
        )
        start = end
    return cues


def timestamp(seconds: float, separator: str = ",") -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{millis:03}"


def write_srt(cues: list[SubtitleCue], output_path: Path) -> Path:
    blocks = [
        f"{cue.index}\n{timestamp(cue.start_seconds)} --> {timestamp(cue.end_seconds)}\n{cue.text}"
        for cue in cues
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return output_path
