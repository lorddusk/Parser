import asyncio
import json
import logging

from lib.copy import checkCopyMeta
from lib.parse.deity import parseDeity, deitySrdFilter, parseDeityCopies
from lib.parsing import render
from lib.utils import dump, get_data, fix_dupes

log = logging.getLogger("deities")

SOURCE_HIERARCHY = ('TCE', 'MOT', 'MTF', 'VGM', 'GGR', 'SCAG', 'DMG', 'UA', 'nil')


def get_latest_deities():
    return get_data("deities.json")['deity']



async def run():
    data = get_latest_deities()
    data = parseDeityCopies(data)
    data = parseDeity(data)
    data = deitySrdFilter(data)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    await dump(data, 'deities.json', md=True)
    # await dump(srdonly(data), 'srd-deities.json')
    # diff('srd/srd-deities.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
