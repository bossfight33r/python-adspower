# python-adspower

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![AdsPower](https://img.shields.io/badge/AdsPower-local%20API-orange)](https://www.adspower.com)

Async Python client for the AdsPower local API.

thin wrapper around the local REST API (`localhost:50325`) — handles the boring stuff: request building, response parsing, retries

Works with SunBrowser and FlowerBrowser, built to use alongside Playwright or Puppeteer.

## Install

```bash
pip install git+https://github.com/bossfighter/python-adspower.git
```

AdsPower desktop app must be running.

## Usage

```python
import asyncio
from adspower import AdsPowerClient, Proxy, WIN_FINGERPRINT

async def main():
    async with AdsPowerClient.from_env() as client:
        profile = await client.profiles.create(
            name="my_account",
            proxy=Proxy.from_url("http://user:pass@1.2.3.4:8080"),
            fingerprint=WIN_FINGERPRINT,
        )
        async with client.browser.session(profile.id) as active:
            print(active.websocket_url)

asyncio.run(main())
```

Set `ADSPOWER_API_KEY` env var or pass `api_key="..."` directly.

### Playwright

```python
from playwright.async_api import async_playwright

async with client.browser.session(profile_id) as active:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(active.websocket_url)
        page = browser.contexts[0].pages[0]
        await page.goto("https://example.com")
```

### Reuse existing session

```python
async with client.browser.ensure_session(profile_id) as active:
    print(active.websocket_url)
```

### Proxy

```python
proxy = Proxy.from_url("socks5://user:pass@1.2.3.4:1080")
# or explicit
proxy = Proxy(host="1.2.3.4", port=1080, user="u", password="p", type="socks5")
```

### Fingerprint

```python
fp = Fingerprint.random("mac")
await client.profiles.create("acc", fingerprint=fp)
```

presets: `WIN_FINGERPRINT`, `MAC_FINGERPRINT`, `LINUX_FINGERPRINT`, `ANDROID_FINGERPRINT`, `IOS_FINGERPRINT`

### Profiles

```python
profiles = await client.profiles.list(group_id="123", tag="farming")
profiles = await client.profiles.search("my_account")

async for profile in client.profiles.iter():
    print(profile.name)

created = await client.profiles.create_many([
    {"name": "main_farm", "proxy": proxy1},
    {"name": "warmup_2", "proxy": proxy2},
])

await client.profiles.update(profile.id, clear_proxy=True)
await client.profiles.update_cookies(profile.id, "[{...}]")
cookie_str = await client.profiles.cookies(profile.id)

tags = await client.profiles.tags()
await client.profiles.delete(profile.id)
```

### Opening multiple profiles

```python
client = AdsPowerClient(api_key="key", concurrency=3)
opened = await client.manager.open_all(["id1", "id2", "id3"])
```

### Health

```python
restarted = await client.health.restart_dead(["id1", "id2", "id3"])
```

### Wait for AdsPower to start

```python
await client.wait_ready(timeout=30.0)
```

## Error handling

```python
from adspower import AdsPowerError, AdsPowerApiError, AdsPowerConnectionError, AdsPowerStuckError

try:
    await client.browser.open(profile_id)
except AdsPowerStuckError:
    print("AdsPower stuck, restart the app")
except AdsPowerConnectionError:
    print("AdsPower not running")
except AdsPowerApiError as e:
    print(f"API error {e.code}: {e}")
```

connection drops and rate limits are retried automatically (tenacity, up to 4 attempts)

## Requirements

- Python 3.11+
- AdsPower desktop app
