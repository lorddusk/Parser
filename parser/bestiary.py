from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio

from lib.copy.copy import checkCopyMeta, regexParsing
from lib.parsing import recursive_tag
from lib.parsingmethods import parse_ac, translate_skills, monster_render, parse_attacks
from lib.utils import *

ATTACK_RE = re.compile(r'(?:<i>)?(?:\w+ ){1,4}Attack:(?:</i>)? ([+-]?\d+) to hit, .*?(?:<i>)?'
                       r'Hit:(?:</i>)? (?:(?:[+-]?\d+ \((.+?)\))|(?:([+-]?\d+))) (\w+) damage[., ]??'
                       r'(?:in melee, or [+-]?\d+ \((.+?)\) (\w+) damage at range[,.]?)?'
                       r'(?: or [+-]?\d+ \((.+?)\) (\w+) damage (?:\w+ ?)+[.,]?)?'
                       r'(?: ?plus [+-]?\d+ \((.+?)\) (\w+) damage)?', re.IGNORECASE)
JUST_DAMAGE_RE = re.compile(r'[+-]?\d+ \((.+?)\) (\w+) damage', re.IGNORECASE)
SKILL_NAMES = ('acrobatics', 'animalHandling', 'arcana', 'athletics', 'deception', 'history', 'initiative', 'insight',
               'intimidation', 'investigation', 'medicine', 'nature', 'perception', 'performance', 'persuasion',
               'religion', 'sleightOfHand', 'stealth', 'survival', 'strength', 'dexterity', 'constitution',
               'intelligence', 'wisdom', 'charisma')

log = logging.getLogger("bestiary")

SOURCE_HIERARCHY = ('TCE', 'ERLW', 'MTF', 'VGM', 'XGE', 'PHB', 'DMG', 'GGR', 'SCAG', 'VRGR', 'UAWGtE', 'UA', 'UAArtificer', 'UAArtificerRevisited', 'nil')


def get_bestiaries_from_web():
    return get_indexed_data('bestiary/', 'monster')


def parse_copies(data):
    monsterTemplate = get_json(f'bestiary/template.json')['monsterTemplate']

    for i, monster in enumerate(data):
        if '_copy' not in monster:
            continue
        original = monster.copy()  # how ironic
        del original['_copy']

        copymeta = monster['_copy']
        if monster['name'] is not None:
            log.info(f"Copying {copymeta['name']} onto {monster['name']} ({monster['source']})...")
            to_copy = next(m for m in data if m['source'].lower() == copymeta['source'].lower() and m['name'].lower() == copymeta['name'].lower())

            data_str = json.dumps(to_copy)
            if copymeta.get('_mod', None) is not None:
                for key, mods in copymeta.get('_mod', []).items():
                    data_str = checkCopyMeta(data_str, key, mods)

            if copymeta.get('_trait', None) is not None:
                meta = copymeta.get('_trait', [])
                to_copy_trait = next(m for m in monsterTemplate if m['source'].lower() == meta['source'].lower() and m['name'].lower() == meta['name'].lower())
                to_copy_trait = to_copy_trait.get('apply', [])
                if to_copy_trait.get('_root', None) is not None:
                    for key, mods in to_copy_trait.get('_root', []).items():
                        data_str = checkCopyMeta(data_str, key, mods)

                if to_copy_trait.get('_mod', None) is not None:
                    for key, mods in to_copy_trait.get('_mod', []).items():
                        data_str = checkCopyMeta(data_str, key, mods)

                data_str = regexParsing(data_str, meta, monster['name'])

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


async def run():
    data = get_bestiaries_from_web()
    data = parse_copies(data)
    data = parse_copies(data)
    data = srdfilter(data)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    data = parse_ac(data)
    data = translate_skills(data)
    rendered = monster_render(data)
    rendered = recursive_tag(rendered)
    out = parse_attacks(rendered)
    await dump(out, 'bestiary.json')

    # await dump(srdonly(data), 'srd-bestiary.json')
    # diff('srd/srd-bestiary.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
