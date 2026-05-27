import pytest
from adspower import Fingerprint, WIN_FINGERPRINT

def test_random_win():
    fp = Fingerprint.random("win")
    assert fp.os == "win" and fp.ua != "" and fp.screen_resolution != "" and fp.webgl_config.unmasked_renderer != ""

def test_to_api_has_required_fields():
    api = Fingerprint.random("win").to_api()
    for key in ("os", "ua", "screen_resolution", "webgl_config", "canvas", "webgl", "audio"):
        assert key in api

def test_template_randomizes_on_each_call():
    assert len({WIN_FINGERPRINT.to_api()["ua"] for _ in range(10)}) > 1

def test_timezone_included_only_when_manual():
    assert Fingerprint(os="win", automatic_timezone="0", timezone="Europe/Berlin").to_api().get("timezone") == "Europe/Berlin"
    assert "timezone" not in Fingerprint(os="win").to_api()

def test_frozen():
    with pytest.raises(Exception): Fingerprint().os = "mac"  # type: ignore[misc]
