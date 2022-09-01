import asyncio
import pprint

from lib.copy import checkCopyMeta, regexParsing
from lib.parsing import recursive_tag, render
from lib.parsingmethods import parse_ac, translate_skills, monster_render, parse_attacks
from lib.utils import *

log = logging.getLogger("bestiaryFluff")

SOURCE_HIERARCHY = ('TCE', 'ERLW', 'MTF', 'VGM', 'XGE', 'PHB', 'DMG', 'GGR', 'SCAG', 'VRGR', 'UAWGtE', 'UA', 'UAArtificer', 'UAArtificerRevisited', 'nil')


def get_bestiaries_from_web():
    return get_indexed_data('bestiary/', 'monsterFluff', fluff=True)


def parse_copies(data):
    for i, monster in enumerate(data):
        if '_copy' not in monster:
            continue
        original = monster.copy()  # how ironic
        del original['_copy']

        copymeta = monster['_copy']
        if monster['name'] is not None:
            log.info(f"Copying {copymeta['name']} onto {monster['name']}...")
            to_copy = next(m for m in data if m['source'].lower() == copymeta['source'].lower() and m['name'].lower() == copymeta['name'].lower())

            data_str = json.dumps(to_copy)
            if copymeta.get('_mod', None) is not None:
                for key, mods in copymeta.get('_mod', []).items():
                    data_str = checkCopyMeta(data_str, key, mods)

            # Todo Traits: scalarMultProp, scalarAddProp, scalarAddHit, scalarAddDc, maxSize, scalarMultXp

            copied = json.loads(data_str)
            copied.update(original)
            data[i] = copied
    return data


def srdfilter(data):
    with open('./srd/srd-monsters.txt') as f:
        srd = [s.strip().lower() for s in f.read().split('\n')]

    for monster in data:
        if monster['name'].lower() in srd:
            monster['srd'] = True
        else:
            monster['srd'] = False
    return data


def recursiveRender(entry, textStack, meta):
    if entry is None:
        return textStack, meta

    if isinstance(entry, dict):
        if entry.get('type', None) == 'section':
            meta['depth'] = -1
        _type = entry.get('type')
        if _type == 'section':
            _type = "entries"
        if _type == "wrapper":
            textStack, meta = recursiveRender(entry.get("wrapper"), textStack, meta)

        meta['_typeStack'].append(_type)

        if _type == "entries":
            nextDepth = meta['depth'] = meta['depth'] + 1 if meta['depth'] < 2 else meta['depth']
            if entry.get("name", None) is not None:
                textStack += f"**{entry.get('name')}**\n"

            if entry.get('entries', None) is not None:
                for entries in entry.get('entries'):
                    meta['depth'] = nextDepth
                    textStack, meta = recursiveRender(entries, textStack, meta)
    elif isinstance(entry, str):
        textStack += f"{entry}\n\n"

    return textStack, meta


def fluff_render(data):
    for fluff in data:
        textStack = ""
        sectionLevel = 0
        if fluff.get("entries", None) is not None:
            entry = fluff.get("entries")
            if isinstance(entry, list):
                for x in entry:
                    meta = {'_typeStack': [], "depth": sectionLevel}
                    textStack, meta = recursiveRender(x, textStack, meta)

            meta = {'_typeStack': [], "depth": 0}
            textStack, meta = recursiveRender(entry, textStack, meta)
        fluff['entries'] = textStack
    return data


async def run():
    data = get_bestiaries_from_web()
    data = parse_copies(data)
    data = fix_dupes(data, SOURCE_HIERARCHY, True)
    data = fluff_render(data)
    data = recursive_tag(data)
    await dump(data, 'bestiaryFluff.json')

    # await dump(srdonly(data), 'srd-bestiary.json')
    # diff('srd/srd-bestiary.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
