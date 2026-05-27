"""
Open an AdsPower profile, connect Playwright via CDP, scrape a page, close.

Usage:
    pip install playwright python-adspower
    playwright install chromium
    python examples/playwright_scrape.py
"""

import asyncio
import os

from playwright.async_api import async_playwright

from adspower import AdsPowerClient, Proxy, WIN_FINGERPRINT

PROFILE_ID = os.environ.get("ADSPOWER_PROFILE_ID", "")


async def main() -> None:
    async with AdsPowerClient.from_env() as client:
        if not await client.ping():
            raise RuntimeError("AdsPower is not running")

        # create a fresh profile if no ID was provided
        if not PROFILE_ID:
            profile = await client.profiles.create(
                name="playwright_example",
                proxy=Proxy.from_url(os.environ.get("PROXY_URL", "")),
                fingerprint=WIN_FINGERPRINT,
            )
            profile_id = profile.id
            print(f"created profile {profile_id!r}")
        else:
            profile_id = PROFILE_ID

        async with client.browser.session(profile_id) as active:
            print(f"browser open: {active.websocket_url}")

            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(active.websocket_url)
                page = browser.contexts[0].pages[0]

                await page.goto("https://httpbin.org/ip")
                body = await page.inner_text("body")
                print("IP response:", body.strip())


if __name__ == "__main__":
    asyncio.run(main())
