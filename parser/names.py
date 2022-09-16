from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.utils import get_data, dump

log = logging.getLogger("names")


def get_names():
    return get_data("names.json")['name']


def clean_tables(names):
    for race in names:
        log.info(f"Parsing names for {race['name']}")
        tables = []
        for table in race['tables']:
            log.info(f"Parsing option {table['option']}")
            new_table = {'name': table['option'], 'choices': []}
            for choice in table['table']:
                new_table['choices'].append(choice['result'])
            tables.append(new_table)
        race['tables'] = tables

    return names


async def run():
    data = get_names()
    data = clean_tables(data)
    await dump(data, 'names.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
