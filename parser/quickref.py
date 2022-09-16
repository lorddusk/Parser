from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio

from lib.parsing import render
from lib.utils import dump, get_data


def get_latest_quickref():
    return get_data("generated/bookref-quick.json")['data']['bookref-quick']

def parse(data):
    out = []
    for raw in data:
        entry = raw['entries']
        for x in entry:
            rule = {
                "name": x['name'],
                "text": render(x['entries']),
                "source": x['source'],
                "page": x.get('page', '?')
            }
            out.append(rule)
    return out

async def run():
    data = get_latest_quickref()
    data = parse(data)
    await dump(data, 'quickref.json')

if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")