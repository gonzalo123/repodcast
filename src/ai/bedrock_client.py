import json
from typing import Protocol

import boto3
from pydantic import ValidationError

from src.ai.prompts import episode_prompt
from src.domain.episode import Episode
from src.domain.repository import RepositorySummary
from src.settings import Settings


class AiClient(Protocol):
    def generate_episode(
        self,
        repository: RepositorySummary,
        title: str | None,
        minutes: int,
        focus: str | None = None,
    ) -> Episode: ...


class BedrockAiClient:
    def __init__(self, settings: Settings) -> None:
        session = boto3.Session(
            profile_name=settings.aws_profile, region_name=settings.aws_region
        )
        self.client = session.client("bedrock-runtime")
        self.model_id = settings.bedrock_model_id

    def generate_episode(
        self,
        repository: RepositorySummary,
        title: str | None,
        minutes: int,
        focus: str | None = None,
    ) -> Episode:
        prompt = episode_prompt(repository, title, minutes, focus)
        response = self.client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.2, "maxTokens": 6000},
        )
        text = response["output"]["message"]["content"][0]["text"]
        try:
            return _episode_from_text(text, minutes)
        except (ValidationError, ValueError, json.JSONDecodeError) as error:
            repair = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {"role": "user", "content": [{"text": prompt}]},
                    {"role": "assistant", "content": [{"text": text}]},
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": (
                                    "The JSON does not satisfy the schema. Fix it and return the complete "
                                    "JSON object only. Every slide MUST contain a non-empty dialogue with "
                                    "host and guest turns; narration must be null. Validation error:\n"
                                    f"{error}"
                                )
                            }
                        ],
                    },
                ],
                inferenceConfig={"temperature": 0, "maxTokens": 6000},
            )
            repaired_text = repair["output"]["message"]["content"][0]["text"]
            return _episode_from_text(repaired_text, minutes)


def _json_payload(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1].rsplit("```", 1)[0]
        if stripped.startswith("json\n"):
            stripped = stripped[5:]
    return stripped


def _episode_from_text(text: str, target_minutes: int) -> Episode:
    payload = json.loads(_json_payload(text))
    if not isinstance(payload, dict):
        raise ValueError("Bedrock response must be a JSON object")
    payload["target_minutes"] = target_minutes
    episode = Episode.model_validate(payload)
    return _normalize_durations(episode, target_minutes * 60)


def _normalize_durations(episode: Episode, target_seconds: int) -> Episode:
    durations = [slide.duration_seconds for slide in episode.slides]
    current_total = sum(durations)
    raw = [duration * target_seconds / current_total for duration in durations]
    normalized = [max(1, int(value)) for value in raw]
    difference = target_seconds - sum(normalized)

    if difference > 0:
        order = sorted(
            range(len(raw)),
            key=lambda index: raw[index] - int(raw[index]),
            reverse=True,
        )
        for offset in range(difference):
            normalized[order[offset % len(order)]] += 1
    elif difference < 0:
        order = sorted(
            range(len(normalized)), key=lambda index: normalized[index], reverse=True
        )
        for offset in range(-difference):
            index = order[offset % len(order)]
            if normalized[index] > 1:
                normalized[index] -= 1

    slides = [
        slide.model_copy(update={"duration_seconds": duration})
        for slide, duration in zip(episode.slides, normalized, strict=True)
    ]
    return episode.model_copy(update={"slides": slides})
