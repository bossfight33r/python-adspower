"""
Open multiple profiles in parallel and check which ones came up healthy.

Usage:
    ADSPOWER_API_KEY=your_key python examples/bulk_open.py
"""

import asyncio

from adspower import AdsPowerClient

PROFILE_IDS = ["id1", "id2", "id3", "id4", "id5"]


async def main() -> None:
    async with AdsPowerClient.from_env(concurrency=3) as client:
        print(f"opening {len(PROFILE_IDS)} profiles (max 3 at a time)...")
        opened = await client.manager.open_all(PROFILE_IDS)
        print(f"opened: {len(opened)}/{len(PROFILE_IDS)}")

        for p in opened:
            print(f"  {p.id}  ws={p.websocket_url}")

        # after some work, check who died and restart them
        print("\nchecking health...")
        restarted = await client.health.restart_dead(PROFILE_IDS)
        if restarted:
            print(f"restarted {len(restarted)} dead profiles: {restarted}")
        else:
            print("all profiles healthy")

        await client.manager.close_all(PROFILE_IDS)


if __name__ == "__main__":
    asyncio.run(main())
