from __future__ import annotations

import logging
import sqlite3

from ..api import ProfilesApi
from ..models import Profile

logger = logging.getLogger(__name__)


class Sync:
    """Links AdsPower profiles to local SQLite accounts by remark/username."""

    def __init__(self, profiles: ProfilesApi, db_path: str):
        self.profiles = profiles
        self.db_path = db_path

    async def pull(self) -> list[Profile]:
        profiles = await self.profiles.list()
        linked = self._link(profiles)
        logger.info(f"profiles: {len(profiles)}, linked: {linked}")
        return profiles

    async def unlinked(self) -> list[Profile]:
        profiles = await self.profiles.list()
        ids = self._linked_ids()
        return [p for p in profiles if p.id not in ids]

    def _link(self, profiles: list[Profile]) -> int:
        linked = 0
        with sqlite3.connect(self.db_path) as conn:
            for p in profiles:
                if self._find_by_adspower(conn, p.id):
                    continue
                acc_id = p.remark and self._find_by_username(conn, p.remark)
                if acc_id:
                    conn.execute(
                        "UPDATE accounts SET adspower_id=? WHERE id=?", (p.id, acc_id)
                    )
                    linked += 1
        return linked

    def _linked_ids(self) -> set[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT adspower_id FROM accounts WHERE adspower_id IS NOT NULL"
            ).fetchall()
        return {r[0] for r in rows}

    def _find_by_adspower(self, conn: sqlite3.Connection, adspower_id: str) -> bool:
        return bool(
            conn.execute(
                "SELECT 1 FROM accounts WHERE adspower_id=?", (adspower_id,)
            ).fetchone()
        )

    def _find_by_username(self, conn: sqlite3.Connection, username: str) -> int | None:
        row = conn.execute(
            "SELECT id FROM accounts WHERE username=?", (username.lstrip("@"),)
        ).fetchone()
        return row[0] if row else None
