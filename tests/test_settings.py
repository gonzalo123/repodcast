from src.settings import Settings


def test_empty_aws_profile_uses_default_credentials() -> None:
    settings = Settings(aws_profile="")

    assert settings.aws_profile is None
