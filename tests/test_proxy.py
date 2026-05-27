import pytest
from pydantic import ValidationError
from adspower import Proxy

def test_from_url_http():
    p = Proxy.from_url("http://user:pass@1.2.3.4:8080")
    assert p.host == "1.2.3.4" and p.port == 8080 and p.user == "user" and p.type == "http"

def test_from_url_socks5():
    p = Proxy.from_url("socks5://1.2.3.4:1080")
    assert p.type == "socks5" and p.user == ""

def test_str_repr():
    assert str(Proxy(host="1.2.3.4", port=8080, user="u", password="p")) == "http://u:p@1.2.3.4:8080"
    assert str(Proxy(host="1.2.3.4", port=8080)) == "http://1.2.3.4:8080"

def test_invalid_port():
    with pytest.raises(ValidationError): Proxy(host="1.2.3.4", port=99999)
