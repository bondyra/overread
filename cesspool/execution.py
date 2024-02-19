import asyncio
from collections import namedtuple


Result = namedtuple("Result", "seq type dimensions things")


def execute(inputs):
    yield from asyncio.run(_match_and_run(inputs))


async def _match_and_run(inputs):
    return await asyncio.gather(*(_execute_input(i) for i in inputs))


async def _execute_input(i):
    return Result(i.seq, i.type, i.dimensions, await i.module.get(i.type, i.dimensions))
