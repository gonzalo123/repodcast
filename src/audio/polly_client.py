import re
from pathlib import Path
from typing import Protocol
from xml.sax.saxutils import escape

import boto3

from src.settings import Settings

_SENTENCE_END = re.compile(r"([.!?])(\s+|$)")


def to_ssml(text: str, prosody_rate: str) -> str:
    escaped = escape(text)
    # ponytail: naive sentence-end detection (splits on . ! ?), doesn't special-case
    # abbreviations like "e.g."; refine if narration text starts hitting that.
    with_breaks = _SENTENCE_END.sub(r'\1<break time="300ms"/>\2', escaped)
    return f'<speak><prosody rate="{prosody_rate}">{with_breaks}</prosody></speak>'


class TtsClient(Protocol):
    def synthesize(
        self,
        text: str,
        output_path: Path,
        duration_seconds: int | None = None,
        voice_id: str | None = None,
    ) -> Path: ...


class PollyTtsClient:
    def __init__(self, settings: Settings) -> None:
        session = boto3.Session(
            profile_name=settings.aws_profile, region_name=settings.aws_region
        )
        self.client = session.client("polly")
        self.voice_id = settings.polly_voice_id
        self.voices = {
            "host": settings.polly_host_voice_id,
            "guest": settings.polly_guest_voice_id,
        }
        self.engine = settings.polly_engine
        self.text_type = settings.polly_text_type
        self.sample_rate = settings.polly_sample_rate
        self.prosody_rate = settings.polly_prosody_rate

    def synthesize(
        self,
        text: str,
        output_path: Path,
        duration_seconds: int | None = None,
        voice_id: str | None = None,
    ) -> Path:
        del duration_seconds
        voice = self.voices.get(voice_id or "", voice_id or self.voice_id)
        payload = to_ssml(text, self.prosody_rate) if self.text_type == "ssml" else text
        response = self.client.synthesize_speech(
            Text=payload,
            OutputFormat="mp3",
            VoiceId=voice,
            Engine=self.engine,
            TextType=self.text_type,
            SampleRate=self.sample_rate,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        stream = response["AudioStream"]
        try:
            output_path.write_bytes(stream.read())
        finally:
            stream.close()
        return output_path
