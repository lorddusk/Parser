from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.parsing import render
from lib.utils import dump, get_data

log = logging.getLogger("psionics")


def get_latest_psionics():
    return get_data("psionics.json")['psionic']


def parse_talent(raw):
    talent = {"name": raw['name'],
              "text": render(raw['entries']),
              "type": raw['type'],
              "source": raw['source'],
              "page": raw.get('page', '?')
              }
    return talent


def parse_discipline(raw):
    modes = []
    for m in raw['modes']:
        if 'concentration' in m:
            mode = {
                "name": m['name'],
                "cost": m['cost'],
                "concentration": m['concentration'],
                "entries": render(m['entries'])
            }
        elif 'cost' in m:
            mode = {
                "name": m['name'],
                "cost": m['cost'],
                "entries": render(m['entries'])
            }
        elif 'submodes' in m:
            smode = []
            for s in m['submodes']:
                sm = {
                    "name": s['name'],
                    "cost": s['cost'],
                    "entries": render(s['entries'])
                }
                smode.append(sm)
            mode = {
                "name": m['name'],
                "entries": render(m['entries']),
                "submodes": smode
            }
        else:
            mode = {}
        modes.append(mode)

    discipline = {"name": raw['name'],
                  "description": raw['entries'],
                  "focus": render(raw['focus']),
                  "modes": modes,
                  "order": raw['order'],
                  "type": raw['type'],
                  "source": raw['source'],
                  "page": raw.get('page', '?')
                  }
    return discipline


def parse(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        if raw['type'] == "T":
            psionic = parse_talent(raw)
        elif raw['type'] == "D":
            psionic = parse_discipline(raw)
        else:
            log.warning(f"Unknown type: {raw['name']}")
            psionic = "{}"
        out.append(psionic)
    return out


async def run():
    data = get_latest_psionics()
    data = parse(data)
    await dump(data, 'psionics.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
