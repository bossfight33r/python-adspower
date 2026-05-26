from __future__ import annotations

import asyncio
import logging

from ..api import BrowserApi

logger = logging.getLogger(__name__)

class Health:
    def __init__(self, browser: BrowserApi, sem: asyncio.Semaphore | None = None):
        self.browser = browser
        self._sem = sem or asyncio.Semaphore(3)

    async def check(self, profile_ids: list[str]) -> dict[str, bool]:
        results = await asyncio.gather(*[self._check_one(pid) for pid in profile_ids], return_exceptions=True)
        return {pid: r if isinstance(r, bool) else False for pid, r in zip(profile_ids, results)}

    async def dead(self, profile_ids: list[str]) -> list[str]:
        return [pid for pid, alive in (await self.check(profile_ids)).items() if not alive]

    async def restart_dead(self, profile_ids: list[str]) -> list[str]:
        dead = await self.dead(profile_ids)
        if not dead: return []
        results = await asyncio.gather(*[self._open_guarded(pid) for pid in dead], return_exceptions=True)
        restarted = [pid for pid, r in zip(dead, results) if not isinstance(r, Exception)]
        logger.info("restarted %d/%d", len(restarted), len(dead))
        return restarted

    async def _check_one(self, profile_id: str) -> bool:
        async with self._sem: return await self.browser.active(profile_id)

    async def _open_guarded(self, profile_id: str) -> None:
        async with self._sem: await self.browser.open(profile_id)
