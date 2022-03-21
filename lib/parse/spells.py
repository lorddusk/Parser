import json
import logging
import sys
from lib.parsing import recursive_tag, render

NEW_AUTOMATION = "oldauto" not in sys.argv
VERB_TRANSFORM = {'dispel': 'dispelled', 'discharge': 'discharged'}
SPELL_AUTOMATION_SRC = "https://raw.githubusercontent.com/avrae/avrae-spells/master/spells.json"
IGNORED_FILES = ('3pp', 'stream')

log = logging.getLogger("spells")

def parsetime(spell):
    timedata = spell['time'][0]
    unit = timedata['unit']
    number = timedata['number'] if timedata.get('number','') is not '' else timedata['amount']

    if unit == 'bonus':
        unit = 'bonus action'
    if number > 1:
        unit = f"{unit}s"
    time = f"{number} {unit}"
    if 'condition' in timedata:
        time = f"{time}, {timedata['condition']}"
    spell['time'] = time
    log.debug(f"{spell['name']} time: {time}")


def plural_to_single(unit):
    return {
        'feet': 'foot'
    }.get(unit, unit.rstrip('s'))


def parserange(spell):
    rangedata = spell['range']
    if rangedata['type'] == 'special':
        range_ = 'Special'
    elif rangedata['type'] == 'point':
        distance = rangedata['distance']
        unit = distance['type']
        if 'amount' in distance:
            if distance['amount'] == 1:
                unit = plural_to_single(unit)
            range_ = f"{distance['amount']} {unit}"
        else:
            range_ = unit.title()
    else:
        distance = rangedata['distance']
        unit = plural_to_single(distance['type'])
        if 'amount' in distance:
            range_ = f"Self ({distance['amount']} {unit} {rangedata['type']})"
        else:
            range_ = f"Self ({unit.title()} {rangedata['type']})"
    spell['range'] = range_
    log.debug(f"{spell['name']} range: {range_}")


def parsecomponents(spell):
    if spell.get('components'):
        compdata = spell['components']
        v = compdata.get('v')
        s = compdata.get('s')
        m = compdata.get('m')
        if isinstance(m, dict):
            parsedm = f"M ({m['text']})"
        elif isinstance(m, bool):
            parsedm = "M"
        else:
            parsedm = f"M ({m})"

        comps = []
        if v:
            comps.append("V")
        if s:
            comps.append("S")
        if m:
            comps.append(parsedm)
        comps = ', '.join(comps)
        spell['components'] = comps
        log.debug(f"{spell['name']} components: {comps}")


def parseduration(spell):
    durdata = spell['duration'][0]
    concentration = durdata.get('concentration', False)
    if durdata['type'] == 'timed':
        unit = durdata['duration']['type']
        number = durdata['duration'].get('amount', 0)
        if number == 0:
            duration = f"{unit}"
        else:
            if number == 1 and unit == "minute":
                unit = f"{unit}"
            else:
                unit = f"{unit}s"
            duration = f"{number} {unit}"
        if concentration:
            duration = f"Concentration, up to {duration}"
        elif durdata['duration'].get('upTo'):
            duration = f"Up to {duration}"
    elif durdata['type'] == 'permanent':
        if durdata.get('ends'):
            duration = f"Until {' or '.join(VERB_TRANSFORM.get(v, v + 'ed') for v in durdata['ends'])}"
        else:
            duration = "Permanent"
    elif durdata['type'] == 'instant':
        duration = "Instantaneous"
    else:
        duration = durdata['type'].title()

    spell['duration'] = duration
    spell['concentration'] = concentration
    log.debug(f"{spell['name']} duration: {duration}")
    log.debug(f"{spell['name']} concentration: {concentration}")


def parseclasses(spell):
    if spell.get('classes') is not None:
        try:
            classes = [c['name'] for c in spell['classes']['fromClassList']]
        except KeyError:
            classes = []
        subclasses = []
        for subclass in spell['classes'].get('fromSubclass', []):
            if '(' in subclass['class']['name'] or '(' in subclass['subclass']['name']:
                continue
            if subclass['class']['name'] in classes:
                continue
            subclasses.append(f"{subclass['class']['name']} ({subclass['subclass']['name']})")
        classes = list(set(classes))
        subclasses = list(set(subclasses))
        spell['classes'] = sorted(classes)
        spell['subclasses'] = sorted(subclasses)
        log.debug(f"{spell['name']} classes: {classes}")
        log.debug(f"{spell['name']} subclasses: {subclasses}")


def ensure_ml_order(spells, srd=False):
    log.info("Attempting to put spells in ML order...")
    try:
        with open(f'in/map-{"srd-" if srd else ""}spell.json') as f:
            spell_map_dict = json.load(f)
    except FileNotFoundError:
        log.warning(f"ML spell map not found. Spell order may not match ML outputs.")
        return spells
    spell_map = sorted(((int(i), name) for i, name in spell_map_dict.items()), key=lambda i: i[0])
    spell_map = [s[1] for s in spell_map]  # index holds position, since one-hot

    # sort spells in map first, then map position, then name
    def spellsort(s):
        try:
            ml_index = spell_map.index(s['name'])
        except ValueError:
            ml_index = -1
        return s['name'] not in spell_map, ml_index, s['name']

    spells = sorted(spells, key=spellsort)
    if len(spells) != len(spell_map):
        log.warning(f"Number of spells differs from spell map length. Delta: {len(spells) - len(spell_map)}")
    return spells


def parseSpells(data):
    processed = []
    for spell in data:
        log.info(f"Parsing {spell['name']}...")
        parsetime(spell)
        parserange(spell)
        parsecomponents(spell)
        parseduration(spell)
        parseclasses(spell)

        ritual = spell.get('meta', {}).get('ritual', False)
        desc = render(spell['entries'])
        if 'entriesHigherLevel' in spell:
            higherlevels = render(spell['entriesHigherLevel']) \
                .replace("**At Higher Levels**: ", "")
        else:
            higherlevels = None

        newspell = {
            "name": spell['name'],
            "level": spell['level'],
            "school": spell['school'],
            "casttime": spell['time'],
            "range": spell['range'],
            "components": spell.get('components', None),
            "duration": spell['duration'],
            "description": desc,
            "classes": spell.get('classes',''),
            "subclasses": spell.get('subclasses',''),
            "ritual": ritual,
            "higherlevels": higherlevels,
            "source": spell['source'],
            "page": spell.get('page', '?'),
            "concentration": spell['concentration']
        }
        processed.append(recursive_tag(newspell))

    processed = ensure_ml_order(processed)
    return processed