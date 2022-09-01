import asyncio
import copy
import logging
from lib.parse.spells import parseSpells
from lib.utils import dump, get_indexed_data, fix_dupes

log = logging.getLogger("spells")

SOURCE_HIERARCHY = ('FTD', 'TCE', 'MTF', 'VGM', 'PHB', 'DMG', 'GGR', 'MOT', 'UA', 'nil')

with open('./srd/srd-spells.txt') as f:
    srd_spells = [s.strip().lower() for s in f.read().split('\n')]


def get_spells():
    return get_indexed_data('spells/', 'spell')


def srdfilter(data):
    transforms = {}
    with open('srd/srd-spells.txt') as f:
        for srdspell in f.read().split('\n'):
            if ':' in srdspell:
                old, new = srdspell.split(':')
            else:
                old = new = srdspell
            transforms[old.lower().strip()] = new.lower().strip()
    found = set()

    for spell in data:
        spell_name = spell['name'].lower()
        if spell_name in transforms:
            if transforms[spell_name] == spell_name:
                spell['srd'] = True
                found.add(spell['name'].lower())
            else:
                new_spell = copy.deepcopy(spell)
                new_spell['name'] = transforms[spell_name].title()
                transforms[transforms[spell_name]] = transforms[spell_name]  # make sure we grab it
                data.append(new_spell)
                spell['srd'] = False
        else:
            spell['srd'] = False

    not_found = [s for s in transforms.values() if s not in found]
    log.warning(f"These SRD spells were not found: {', '.join(not_found)}")
    return data


async def run():
    data = get_spells()
    data = parseSpells(data)
    data = srdfilter(data)
    data = fix_dupes(data, SOURCE_HIERARCHY, True)
    await dump(data, 'spells.json', md=True)


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")