import pytest
from pydantic import ValidationError
from adspower import ActiveProfile, Profile, Proxy

def test_profile_label_prefers_remark():
    assert Profile(id="abc", name="account1", remark="Main account").label == "Main account"

def test_profile_requires_nonempty_id():
    with pytest.raises(ValidationError): Profile(id="", name="x")

def test_profile_with_proxy():
    assert "1.2.3.4" in repr(Profile(id="x", name="y", proxy=Proxy(host="1.2.3.4", port=8080)))

def test_active_profile_requires_websocket():
    with pytest.raises(ValidationError): ActiveProfile(id="x", name="y", websocket_url="", debug_port=9222)
