import asyncio
import logging

from lib.parsing import render
from lib.utils import dump, get_data, fix_dupes

log = logging.getLogger("cultsboons")

TYPES = {"MECH": "Mechinal", "MAG": "Magical", "SMPL": "Simple", "CMPX": "Complex", "WTH": "Weather",
         "ENV": "Environmental", "WLD": "Wilderness", "GEN": "Generic"}

SOURCE_HIERARCHY = ('TCE', 'MTF', 'VGM', 'GGR', 'SCAG', 'DMG', 'UA', 'nil')


def get_latest_cults():
    return get_data("cultsboons.json")['cult']


def get_latest_boons():
    return get_data("cultsboons.json")['boon']


def parse_cults(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        cult = {
            "name": raw['name'],
            "text": render(raw['entries']),

            "goal": render(raw.get('goal', '')),
            "cultists": render(raw.get('cultists', '')),
            "signaturespells": render(raw.get('signaturespells', '')),

            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        if cult['goal'] == "":
            cult.pop('goal', None)
        if cult['cultists'] == "":
            cult.pop('cultists', None)
        if cult['signaturespells'] == "":
            cult.pop('signaturespells', None)
        out.append(cult)
    return out


def parse_boons(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        boon = {
            "name": raw['name'],
            "type": raw['type'],
            "text": render(raw['entries']),

            "ability": render(raw.get('ability', '')),
            "signaturespells": render(raw.get('signaturespells', '')),

            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        if boon['ability'] == "":
            boon.pop('ability', None)
        if boon['signaturespells'] == "":
            boon.pop('signaturespells', None)
        out.append(boon)
    return out


async def run():
    data = get_latest_cults()
    data = parse_cults(data)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    await dump(data, 'cults.json')
    data = get_latest_boons()
    data = parse_boons(data)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    await dump(data, 'boons.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")