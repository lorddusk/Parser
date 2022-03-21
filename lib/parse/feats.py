import logging

from lib.parsing import render, ABILITY_MAP
from lib.utils import english_join

log = logging.getLogger("feats")


def parse_prereq(feat):
    prereq = []

    if 'prerequisite' in feat:
        for entry in feat['prerequisite']:
            if 'race' in entry:
                prereq.append(english_join(
                    f"{r['name']}" + (f" ({r['subrace']})" if 'subrace' in r else '') for r in entry['race']))
            if 'ability' in entry:
                abilities = []
                for ab in entry['ability']:
                    abilities.extend(f"{ABILITY_MAP.get(a)} {s}" for a, s in ab.items())
                prereq.append(english_join(abilities))
            if 'spellcasting' in entry:
                prereq.append("The ability to cast at least one spell")
            if 'proficiency' in entry:
                try:
                    prereq.append(f"Proficiency with {entry['proficiency'][0]['armor']} armor")
                except KeyError:
                    prereq.append(f"Proficiency with {entry['proficiency'][0]['weapon']} weapons")
            if 'level' in entry:
                print(entry)
                prereq.append(f"Level {entry['level']}")
            if 'special' in entry:
                prereq.append(entry['special'])
            if 'other' in entry:
                prereq.append(entry['other'].capitalize())

    if prereq:
        return '\n'.join(prereq)
    return None


def parse_ability(feat):
    ability = None
    if 'ability' in feat:
        if 'choose' in str(feat['ability']):
            ability = english_join(ABILITY_MAP.get(a) for a in feat['ability'][0]['choose']['from'])
        else:
            ability = english_join(ABILITY_MAP.get(key) for a in feat['ability'] for key in a)
    return ability


def parseFeats(data):
    out = []
    for feat in data:
        log.info(feat['name'])
        desc = render(feat['entries'])
        prereq = parse_prereq(feat)
        ability = parse_ability(feat)

        new_feat = {
            "name": feat['name'],
            "prerequisite": prereq,
            "source": feat['source'],
            "page": feat.get('page',0),
            "desc": desc,
            "ability": ability
        }
        out.append(new_feat)
    return out