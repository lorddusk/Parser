from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.parsing import render
from lib.utils import dump, get_data

log = logging.getLogger("rewards")

def get_latest_rewards():
    return get_data("rewards.json")['reward']

def parse_rewards(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        reward = {
            "name": raw['name'],
            "type": raw.get('type', ''),
            "text": render(raw['entries']),
            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        out.append(reward)
    return out


async def run():
    data = get_latest_rewards()
    data = parse_rewards(data)
    await dump(data, 'rewards.json')

if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")