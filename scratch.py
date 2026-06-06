# temp
import asyncio
from adspower import AdsPowerClient

async def main():
    async with AdsPowerClient(api_key="xxx") as c:
        profiles = await c.profiles.list()
        for p in profiles:
            print(p.id, p.name)

asyncio.run(main())
