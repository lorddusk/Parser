import asyncio
import copy
import json
import logging

from lib.parse.race import parseRaceCopies, splitSubraces
from lib.utils import diff, dump, explicit_sources, fix_dupes, get_data, remove_ignored, srdonly

SRD = ('Dragonborn', 'Half-Elf', 'Half-Orc', 'Elf (High)', 'Dwarf (Hill)', 'Human', 'Human (Variant)',
       'Halfling (Lightfoot)', 'Gnome (Rock)', 'Tiefling')
SOURCE_HIERARCHY = ('TCE', 'MTF', 'VGM', 'PHB', 'DMG', 'GGR', 'MOT', 'VRGR', 'UA', 'nil')
IGNORED_SOURCES = ('UARacesOfRavnica', 'UACentaursMinotaurs', 'UAEladrinAndGith', 'UAFiendishOptions', 'UAWGE')
EXPLICIT_SOURCES = ('ERLW', 'UAEberron', 'DMG')

log = logging.getLogger("races")


def get_races_from_web():
    return get_data('races.json')['race']


def srdfilter(data):
    for race in data:
        if race['name'] in SRD:
            race['srd'] = True
        else:
            race['srd'] = False
    return data

async def run():
    data = get_races_from_web()
    data = parseRaceCopies(data)
    data = splitSubraces(data)
    data = explicit_sources(data, EXPLICIT_SOURCES)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    data = remove_ignored(data, IGNORED_SOURCES)
    data = srdfilter(data)
    await dump(data, 'races.json')
    # await dump(srdonly(data), 'srd-races.json')
    # diff('srd/srd-races.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
