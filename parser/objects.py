from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.parsing import render
from lib.utils import dump, get_data

log = logging.getLogger("objects")

SIZES = {"T": "Tiny", "S": "Small", "M": "Medium", "L": "Large", "H": "Huge", "G": "Gargantuan", "V": "Varies"}
TYPES = {"SW": "Siege Weapon", "GEN": "GEN", "U": "U"}


def get_latest_objects():
    return get_data("objects.json")['object']


def parse(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        object = {"name": raw['name'],
                  "size": parse_size(raw.get('size')),
                  "type": TYPES.get(raw.get('type')),
                  "ac": raw['ac'],
                  "hp": raw['hp'],
                  "immune": raw['immune'],
                  "resist": raw['resist'] if raw.get('resist') is not None else "",
                  "vulnerable": raw['vulnerable'] if raw.get('vulnerable') is not None else "",
                  "text": render(raw['entries']) if raw.get('entries') is not None else "",
                  "action": raw['actionEntries'] if raw.get('actionEntries') is not None else "",
                  "source": raw['source'],
                  "page": raw['page'] if raw.get('page') is not None else ""}
        if object['resist'] == "":
            object.pop('resist', None)
        if object['vulnerable'] == "":
            object.pop('vulnerable', None)
        if object['action'] == "":
            object.pop('action', None)
        out.append(object)
    return out

def parse_size(data):
    size = []
    for raw in data:
        size.append(SIZES.get(raw))
    return size


def parse_attacks(data):
    for object in data:
        try:
            name = object['action'][0]['name']
        except KeyError as e:
            continue
        except IndexError as e:
            continue

        try:
            raw = object['action'][0]['text']
        except KeyError:
            raw = object['action'][0]['entries'][0]

        if isinstance(raw, dict):
            entries = '{@atk ' + raw['attackType'].lower() + '} ' + raw['attackEntries'][0] + ' {@h}' + \
                      raw['hitEntries'][0]
            action = {
                "name": name,
                "entries": entries
            }
        else:
            action = {
                "name": name,
                "entries": raw
            }

        log.debug(f"Parsed actions for {object['name']}: {action}")
        object['action'] = render(action)
    return data


async def run():
    data = get_latest_objects()
    out = parse(data)
    out = parse_attacks(out)
    await dump(out, 'objects.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
