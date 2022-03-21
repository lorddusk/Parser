import asyncio
import json
import logging

from lib.copy import checkCopyMeta
from lib.parse.backgrounds import parseBackgrounds, srdfilter
from lib.utils import dump, get_data, fix_dupes

log = logging.getLogger("backgrounds")

BASIC = ['Criminal', 'Folk Hero', 'Noble', 'Sage', 'Soldier']

SOURCE_HIERARCHY = ('TCE', 'XGE', 'PHB', 'ERLW', 'VRGR', 'UA', 'nil')


def get_latest_backgrounds():
    return get_data("backgrounds.json")['background']


def parse_copies(data):
    for i, background in enumerate(data):
        if '_copy' not in background:
            continue
        original = background.copy()  # how ironic
        del original['_copy']

        copymeta = background['_copy']
        log.info(f"Copying {copymeta['name']} onto {background['name']}...")
        to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])

        data_str = json.dumps(to_copy)
        if copymeta.get('_mod', None) is not None:
            for key, mods in copymeta.get('_mod', []).items():
                data_str = checkCopyMeta(data_str, key, mods)

        if to_copy.get("_copy", None) is not None:
            copymeta = to_copy['_copy']
            to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])

            data_str = json.dumps(to_copy)
            if copymeta.get('_mod', None) is not None:
                for key, mods in copymeta.get('_mod', []).items():
                    data_str = checkCopyMeta(data_str, key, mods)

        copied = json.loads(data_str)
        copied.update(original)
        data[i] = copied

    return data


async def run():
    data = get_latest_backgrounds()
    data = parse_copies(data)
    data = parseBackgrounds(data)
    data = srdfilter(data)
    data = fix_dupes(data, SOURCE_HIERARCHY, True)
    await dump(data, 'backgrounds.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
