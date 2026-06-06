import json
import pytest
import respx
import httpx

from adspower import AdsPowerClient, ActiveProfile, AdsPowerApiError, AdsPowerConnectionError
from adspower.api.browser import BrowserApi
from adspower.api.profiles import ProfilesApi

BASE = "http://local.adspower.net:50325"

def make_browser_api():
    http = httpx.AsyncClient()
    return http, BrowserApi(http, BASE, {}, {})

def make_profiles_api():
    http = httpx.AsyncClient()
    return http, ProfilesApi(http, BASE, {}, {})

def _ok(data):
    return httpx.Response(200, json={"code": 0, "data": data})

BROWSER_START = {"ws": {"puppeteer": "ws://localhost:9222/abc"}, "debug_port": "9222"}

@respx.mock
async def test_browser_open():
    respx.get(f"{BASE}/api/v1/browser/start").mock(return_value=_ok(BROWSER_START))
    _, api = make_browser_api()
    p = await api.open("profile_123")
    assert isinstance(p, ActiveProfile) and p.debug_port == 9222

@respx.mock
async def test_session_closes_on_exit():
    respx.get(f"{BASE}/api/v1/browser/start").mock(return_value=_ok(BROWSER_START))
    close = respx.get(f"{BASE}/api/v1/browser/stop").mock(return_value=_ok({}))
    _, api = make_browser_api()
    async with api.session("profile_123"): pass
    assert close.called

@respx.mock
async def test_session_closes_on_exception():
    respx.get(f"{BASE}/api/v1/browser/start").mock(return_value=_ok(BROWSER_START))
    close = respx.get(f"{BASE}/api/v1/browser/stop").mock(return_value=_ok({}))
    _, api = make_browser_api()
    with pytest.raises(RuntimeError):
        async with api.session("profile_123"): raise RuntimeError("oops")
    assert close.called

@respx.mock
async def test_profiles_list():
    respx.post(f"{BASE}/api/v2/browser-profile/list").mock(return_value=_ok({"list": [
        {"profile_id": "id1", "name": "acc1", "remark": "", "group_name": ""},
        {"profile_id": "id2", "name": "acc2", "remark": "", "group_name": ""},
    ]}))
    _, api = make_profiles_api()
    profiles = await api.list(size=100)
    assert len(profiles) == 2 and profiles[0].id == "id1"

# @respx.mock
# async def test_profiles_search_returns_matching():
#     # TODO: написать когда разберусь как мокать несколько страниц
#     pass

@respx.mock
async def test_profiles_create():
    respx.post(f"{BASE}/api/v1/user/create").mock(return_value=_ok({"id": "new_id"}))
    _, api = make_profiles_api()
    p = await api.create(name="test_account")
    assert p.id == "new_id" and p.name == "test_account"

@respx.mock
async def test_profiles_delete():
    route = respx.post(f"{BASE}/api/v1/user/delete").mock(return_value=_ok({}))
    _, api = make_profiles_api()
    await api.delete("profile_123")
    assert route.called

@respx.mock
async def test_profiles_update_clear_proxy():
    route = respx.post(f"{BASE}/api/v1/user/update").mock(return_value=_ok({}))
    _, api = make_profiles_api()
    await api.update("profile_123", clear_proxy=True)
    assert json.loads(route.calls[0].request.content)["user_proxy_config"]["proxy_soft"] == "no_proxy"

@respx.mock
async def test_api_error_code():
    respx.post(f"{BASE}/api/v2/browser-profile/list").mock(return_value=httpx.Response(200, json={"code": -1, "msg": "invalid key"}))
    _, api = make_profiles_api()
    with pytest.raises(AdsPowerApiError) as exc_info: await api.list()
    assert exc_info.value.code == -1

def test_from_env(monkeypatch):
    monkeypatch.setenv("ADSPOWER_API_KEY", "key123")
    assert AdsPowerClient.from_env()._base_params.get("serial_number") == "key123"

def test_from_env_override(monkeypatch):
    monkeypatch.setenv("ADSPOWER_API_KEY", "env_key")
    assert AdsPowerClient.from_env(api_key="override")._base_params.get("serial_number") == "override"

def test_concurrency_zero_raises():
    with pytest.raises(ValueError): AdsPowerClient(concurrency=0)

@respx.mock
async def test_wait_ready_timeout():
    respx.post(f"{BASE}/api/v2/browser-profile/list").mock(return_value=httpx.Response(503))
    async with AdsPowerClient() as client:
        with pytest.raises(AdsPowerConnectionError):
            await client.wait_ready(timeout=0.1, interval=0.01)
