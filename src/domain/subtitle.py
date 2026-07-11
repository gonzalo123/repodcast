from pydantic import BaseModel, ConfigDict, Field


class SubtitleCue(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1)
