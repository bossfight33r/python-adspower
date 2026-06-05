from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Literal

from ..models import DEFAULT_FINGERPRINT, Fingerprint, Profile, Proxy
from .base import BaseApi

logger = logging.getLogger(__name__)
BrowserType = Literal["SunBrowser", "FlowerBrowser"]
_MAX_PAGES = 100

class ProfilesApi(BaseApi):
    async def list(self, page: int = 1, size: int = 100, group_id: str | None = None, tag: str | None = None) -> list[Profile]:
        all_profiles: list[Profile] = []
        body: dict[str, Any] = {"page": page, "page_size": size}
        if group_id is not None: body["group_id"] = group_id
        if tag is not None: body["tag"] = tag
        current_page = page
        while current_page <= page + _MAX_PAGES:
            body["page"] = current_page
            data = await self._post("/api/v2/browser-profile/list", body)
            batch = [self._parse(p) for p in data.get("list", [])]
            all_profiles.extend(batch)
            if len(batch) < size: break
            current_page += 1
        else:
            logger.warning("reached page limit (%d), list may be incomplete", _MAX_PAGES)
        return all_profiles

    async def iter(self, size: int = 100, group_id: str | None = None, tag: str | None = None) -> AsyncIterator[Profile]:
        page = 1
        while True:
            body: dict[str, Any] = {"page": page, "page_size": size}
            if group_id is not None: body["group_id"] = group_id
            if tag is not None: body["tag"] = tag
            data = await self._post("/api/v2/browser-profile/list", body)
            batch = [self._parse(p) for p in data.get("list", [])]
            for profile in batch: yield profile  # type: ignore[misc]
            if len(batch) < size: break
            page += 1

    async def create(self, name: str, remark: str = "", group_id: str = "0", proxy: Proxy | None = None,
                     fingerprint: Fingerprint = DEFAULT_FINGERPRINT, browser_type: BrowserType = "SunBrowser",
                     cookie: str = "", tags: list[str] | None = None, open_urls: list[str] | None = None,
                     ip_checker: str = "ip2location", random_fingerprint: bool = False) -> Profile:
        body: dict[str, Any] = {
            "name": name, "remark": remark, "group_id": group_id, "browser_type": browser_type,
            "user_proxy_config": {"proxy_soft": "no_proxy", "ip_checker": ip_checker},
            "fingerprint_config": fingerprint.to_api(),
        }
        if proxy: body["user_proxy_config"] = _proxy_body(proxy, ip_checker)
        if cookie: body["cookie"] = cookie
        if tags: body["tags"] = tags
        if open_urls: body["open_urls"] = open_urls
        if random_fingerprint: body["random_ua"] = "1"
        data = await self._post("/api/v1/user/create", body)
        profile = Profile(id=data["id"], name=name, remark=remark, proxy=proxy)
        logger.info("created %r (os=%s, browser=%s)", profile, fingerprint.os, browser_type)
        return profile

    async def create_many(self, profiles: list[dict[str, Any]], concurrency: int = 3) -> list[Profile]:
        sem = asyncio.Semaphore(concurrency)
        async def _one(kw: dict[str, Any]) -> Profile:
            async with sem: return await self.create(**kw)
        results = await asyncio.gather(*[_one(p) for p in profiles], return_exceptions=True)  # type: ignore[attr-defined]
        failed = sum(1 for r in results if isinstance(r, Exception))
        if failed: logger.error("failed to create %d/%d profiles", failed, len(results))
        return [r for r in results if isinstance(r, Profile)]

    async def update(self, profile_id: str, name: str | None = None, remark: str | None = None,
                     group_id: str | None = None, proxy: Proxy | None = None, clear_proxy: bool = False,
                     fingerprint: Fingerprint | None = None, cookie: str | None = None,
                     tags: list[str] | None = None, open_urls: list[str] | None = None,
                     random_fingerprint: bool | None = None, ip_checker: str | None = None) -> None:
        body: dict[str, Any] = {"user_id": profile_id}
        if name is not None: body["name"] = name
        if remark is not None: body["remark"] = remark
        if group_id is not None: body["group_id"] = group_id
        if fingerprint is not None: body["fingerprint_config"] = fingerprint.to_api()
        if cookie is not None: body["cookie"] = cookie
        if clear_proxy: body["user_proxy_config"] = {"proxy_soft": "no_proxy", "ip_checker": ip_checker or "ip2location"}
        elif proxy is not None: body["user_proxy_config"] = _proxy_body(proxy, ip_checker or "ip2location")
        if tags is not None: body["tags"] = tags
        if open_urls is not None: body["open_urls"] = open_urls
        if random_fingerprint is not None: body["random_ua"] = "1" if random_fingerprint else "0"
        await self._post("/api/v1/user/update", body)
        logger.info("updated %r", profile_id)

    async def update_cookies(self, profile_id: str, cookie: str) -> None:
        await self._post("/api/v1/user/update", {"user_id": profile_id, "cookie": cookie})

    async def update_proxy(self, profile_id: str, proxy: Proxy, ip_checker: str = "ip2location") -> None:
        await self._post("/api/v1/user/update", {"user_id": profile_id, "user_proxy_config": _proxy_body(proxy, ip_checker)})

    async def delete(self, profile_id: str) -> None:
        await self._post("/api/v1/user/delete", {"user_ids": [profile_id]})

    async def delete_many(self, profile_ids: list[str]) -> None:
        if not profile_ids: return
        await self._post("/api/v1/user/delete", {"user_ids": profile_ids})

    async def get(self, profile_id: str) -> Profile | None:
        return next((p for p in await self.list() if p.id == profile_id), None)

    async def search(self, name: str, group_id: str | None = None, tag: str | None = None) -> list[Profile]:
        needle = name.lower()
        return [p for p in await self.list(group_id=group_id, tag=tag) if needle in p.name.lower()]

    async def cookies(self, profile_id: str) -> str:
        # TODO: нет отдельного эндпоинта — тянем весь список, неэффективно
        data = await self._post("/api/v2/browser-profile/list", {"page": 1, "page_size": 100})
        for item in data.get("list", []):
            if (item.get("profile_id") or item.get("user_id")) == profile_id:
                return str(item.get("cookie", ""))
        return ""

    async def tags(self) -> list[str]:
        data = await self._post("/api/v1/tag/list", {"page": 1, "page_size": 100})
        return [str(t.get("name", "")) for t in data.get("list", [])]

    async def groups(self) -> list[dict[str, Any]]:
        all_groups: list[dict[str, Any]] = []
        page = 1
        while True:
            data = await self._post("/api/v1/group/list", {"page": page, "page_size": 100})
            batch = data.get("list", [])
            all_groups.extend(batch)
            if len(batch) < 100: break
            page += 1
        return all_groups

    async def create_group(self, name: str) -> str:
        data = await self._post("/api/v1/group/create", {"group_name": name})
        return str(data.get("group_id", ""))

    async def delete_group(self, group_id: str) -> None:
        await self._post("/api/v1/group/delete", {"group_id": group_id})

    @staticmethod
    def _parse(p: dict[str, Any]) -> Profile:
        pid = p.get("profile_id") or p.get("user_id")
        if not pid: raise ValueError(f"profile response has no id: {p}")
        proxy = None
        cfg = p.get("user_proxy_config") or {}
        if cfg.get("proxy_host"):
            port = int(cfg.get("proxy_port") or 0)
            if port == 0:
                logger.warning("profile %r has proxy_host but missing proxy_port — proxy skipped", pid)
            else:
                proxy = Proxy(host=cfg["proxy_host"], port=port, user=cfg.get("proxy_user", ""),
                              password=cfg.get("proxy_password", ""), type=cfg.get("proxy_type", "http"))
        return Profile(id=pid, name=p.get("name", "") or pid, remark=p.get("remark", ""),
                       group=p.get("group_name", ""), proxy=proxy)

def _proxy_body(proxy: Proxy, ip_checker: str = "ip2location") -> dict[str, str]:
    return {"proxy_soft": "other", "proxy_type": proxy.type, "proxy_host": proxy.host,
            "proxy_port": str(proxy.port), "proxy_user": proxy.user,
            "proxy_password": proxy.password, "ip_checker": ip_checker}
