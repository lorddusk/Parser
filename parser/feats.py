from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.parse.feats import parseFeats
from lib.utils import get_data, dump, fix_dupes

log = logging.getLogger("feats")

SOURCE_HIERARCHY = ('TCE', 'XGE', 'PHB', 'ERLW', 'UA', 'nil')


def get_latest_feats():
    return get_data("feats.json")['feat']


def srdfilter(data):
    for feat in data:
        if feat['name'].lower() == 'grappler':
            feat['srd'] = True
        else:
            feat['srd'] = False
    return data


async def run():
    data = get_latest_feats()
    data = parseFeats(data)
    data = srdfilter(data)
    data = fix_dupes(data, SOURCE_HIERARCHY, True)
    await dump(data, 'feats.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
