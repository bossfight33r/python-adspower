# python-adspower

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![AdsPower](https://img.shields.io/badge/AdsPower-local%20API-orange)](https://www.adspower.com)

Async Python client for the AdsPower local API.

thin wrapper around the local REST API (`localhost:50325`) — handles the boring stuff: request building, response parsing, retries.

Works with SunBrowser and FlowerBrowser. Built to be used with Playwright or Puppeteer.

## Install

```bash
pip install git+https://github.com/bossfighter/python-adspower.git
```

Requries AdsPower to be running.

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

Set `ADSPOWER_API_KEY` or pass `api_key="..."` directly.

### Playwright

```python
from playwright.async_api import async_playwright

async with client.browser.session(profile_id) as active:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(active.websocket_url)
        page = browser.contexts[0].pages[0]
        await page.goto("https://example.com")
```

### Proxy

```python
proxy = Proxy.from_url("socks5://user:pass@1.2.3.4:1080")
proxy = Proxy(host="1.2.3.4", port=1080, user="u", password="p", type="socks5")
```

### Fingerprint

```python
fp = Fingerprint.random("mac")
await client.profiles.create("acc", fingerprint=fp)
```

Presets: `WIN_FINGERPRINT`, `MAC_FINGERPRINT`, `LINUX_FINGERPRINT`, `ANDROID_FINGERPRINT`, `IOS_FINGERPRINT`.

### Profiles

```python
profiles = await client.profiles.list(group_id="123", tag="farming")
await client.profiles.update_cookies(profile.id, "[{...}]")
await client.profiles.update_proxy(profile.id, new_proxy)
await client.profiles.delete(profile.id)
```

### Bulk / concurrency

```python
client = AdsPowerClient(api_key="key", concurrency=3)
opened = await client.manager.open_all(["id1", "id2", "id3"])
```

### Health check

```python
restarted = await client.health.restart_dead(["id1", "id2", "id3"])
```

## Error handling

```python
from adspower import AdsPowerError, AdsPowerApiError, AdsPowerConnectionError

try:
    await client.browser.open(profile_id)
except AdsPowerConnectionError:
    print("AdsPower is not running")
except AdsPowerApiError as e:
    print(f"API error {e.code}: {e}")
```

Connection drops and rate limits are retried automatically.

## Requirements

- Python 3.11+
- AdsPower desktop app
