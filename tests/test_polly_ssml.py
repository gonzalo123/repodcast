from src.audio.polly_client import to_ssml


def test_wraps_in_speak_and_prosody() -> None:
    ssml = to_ssml("Hello world", "medium")
    assert ssml.startswith('<speak><prosody rate="medium">')
    assert ssml.endswith("</prosody></speak>")


def test_inserts_break_after_sentences() -> None:
    ssml = to_ssml("Hello. World?", "medium")
    assert '.<break time="300ms"/> World?<break time="300ms"/>' in ssml


def test_escapes_xml_special_characters() -> None:
    ssml = to_ssml("a & b < c > d", "medium")
    assert "&amp;" in ssml
    assert "&lt;" in ssml
    assert "&gt;" in ssml
    assert "<c>" not in ssml
