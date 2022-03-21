import asyncio
import logging

from lib.parsing import render
from lib.utils import dump, get_data

log = logging.getLogger("trapshazards")

TYPES = {"MECH": "Mechinal", "MAG": "Magical", "SMPL": "Simple", "CMPX": "Complex", "WTH": "Weather", "ENV": "Environmental", "WLD": "Wilderness", "GEN": "Generic"}

def get_latest_traps():
    return get_data("trapshazards.json")['trap']

def get_latest_hazards():
    return get_data("trapshazards.json")['hazard']


def parse_traps(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        trap = {
            "name": raw['name'],
            "type": raw['trapHazType'],
            "tier": raw.get('tier', ''),
            "threat": raw.get('threat', ''),
            "text": render(raw['entries']),

            "trigger": render(raw.get('trigger', '')),

            "initiative": render(raw.get('initiative', '')),
            "initiativeNote": render(raw.get('initiativeNote', '')),

            "effect": render(raw.get('effect', '')),
            "eActive": render(raw.get('eActive', '')),
            "eDynamic": render(raw.get('eDynamic', '')),
            "eConstant": render(raw.get('eConstant', '')),

            "countermeasures": render(raw.get('countermeasures', '')),


            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        if trap['tier'] == "":
            trap.pop('tier', None)
        if trap['threat'] == "":
            trap.pop('threat', None)
        if trap['trigger'] == "":
            trap.pop('trigger', None)
        if trap['initiative'] == "":
            trap.pop('initiative', None)
        if trap['initiativeNote'] == "":
            trap.pop('initiativeNote', None)
        if trap['effect'] == "":
            trap.pop('effect', None)
        if trap['eActive'] == "":
            trap.pop('eActive', None)
        if trap['eDynamic'] == "":
            trap.pop('eDynamic', None)
        if trap['eConstant'] == "":
            trap.pop('eConstant', None)
        if trap['countermeasures'] == "":
            trap.pop('countermeasures', None)
        out.append(trap)
    return out

def parse_hazards(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        hazard = {
            "name": raw['name'],
            "type": raw.get('trapHazType', ''),
            "text": render(raw['entries']),
            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        if hazard['type'] == "":
            hazard.pop('type', None)
        out.append(hazard)
    return out


async def run():
    data = get_latest_traps()
    data = parse_traps(data)
    await dump(data, 'traps.json')
    data = get_latest_hazards()
    data = parse_hazards(data)
    await dump(data, 'hazards.json')

if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")