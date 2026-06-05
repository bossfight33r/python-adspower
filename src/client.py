from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from .api import BrowserApi, ProfilesApi
from .exceptions import AdsPowerConnectionError
from .services import Health, Manager

LOCAL = "http://local.adspower.net:50325"
CLOUD = "https://api.adspower.com"

class AdsPowerClient:
    def __init__(self, api_key: str = "", local: bool = True, concurrency: int = 3):
        if concurrency < 1: raise ValueError("concurrency must be >= 1")
        base = LOCAL if local else CLOUD
        headers = {} if local else {"Authorization": f"Bearer {api_key}"}
        base_params = {"serial_number": api_key} if local else {}
        mounts = {"http://local.adspower.net": None} if local else {}
        self.http = httpx.AsyncClient(timeout=30.0, mounts=mounts)
        self.browser  = BrowserApi(self.http, base, headers, base_params)
        self.profiles = ProfilesApi(self.http, base, headers, base_params)
        sem = asyncio.Semaphore(concurrency)
        self.manager = Manager(self.browser, sem)
        self.health  = Health(self.browser, sem)
        self._base        = base
        self._base_params = base_params
        self._headers     = headers

    @classmethod
    def from_env(cls, **kwargs: Any) -> "AdsPowerClient":
        api_key = kwargs.pop("api_key", os.environ.get("ADSPOWER_API_KEY", ""))
        return cls(api_key=api_key, **kwargs)

    async def ping(self) -> bool:
        try:
            r = await self.http.post(f"{self._base}/api/v2/browser-profile/list",
                headers=self._headers, params=self._base_params,
                json={"page": 1, "page_size": 1}, timeout=5.0)
            return r.status_code == 200
        except httpx.RequestError: return False

    async def wait_ready(self, timeout: float = 30.0, interval: float = 1.0) -> None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while not await self.ping():
            if loop.time() >= deadline:
                raise AdsPowerConnectionError(f"AdsPower not ready after {timeout}s")
            await asyncio.sleep(interval)

    async def shutdown(self) -> None: await self.http.aclose()
    async def __aenter__(self) -> "AdsPowerClient": return self
    async def __aexit__(self, *_: object) -> None: await self.shutdown()
