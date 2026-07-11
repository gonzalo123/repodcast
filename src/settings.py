from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_profile: str | None = None
    aws_region: str = "eu-west-1"
    bedrock_model_id: str = "eu.anthropic.claude-sonnet-4-6"
    polly_voice_id: str = "Joanna"
    polly_host_voice_id: str = "Joanna"
    polly_guest_voice_id: str = "Matthew"
    polly_engine: str = "neural"
    polly_text_type: str = "text"
    polly_sample_rate: str = "24000"
    polly_prosody_rate: str = "medium"
    remotion_command: str = "npx remotion"
    max_file_bytes: int = 100_000
    max_excerpt_chars: int = 4_000

    @field_validator("aws_profile", mode="before")
    @classmethod
    def empty_profile_uses_default_credentials(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value
