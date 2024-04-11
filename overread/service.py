import asyncio

from overread import modules


def load_modules():
    return asyncio.run(_load_modules())


async def _load_modules():
    return [_ async for _ in modules.load()]
