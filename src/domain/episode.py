from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.slide import Slide


class Episode(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1)
    target_minutes: int = Field(gt=0)
    slides: list[Slide] = Field(min_length=1)
    source_commit: str | None = None
    source_url: str | None = None
    source_repository: str | None = None
    intro_duration_seconds: int = Field(default=4, ge=0)

    @model_validator(mode="after")
    def indexes_are_sequential(self) -> "Episode":
        indexes = [slide.index for slide in self.slides]
        if indexes != list(range(1, len(indexes) + 1)):
            raise ValueError("slide indexes must start at 1 and be sequential")
        return self
