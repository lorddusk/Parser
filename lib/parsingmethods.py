import logging
import re

from lib.parsing import render, recursive_tag
from lib.utils import *

log = logging.getLogger(__name__)

SKILL_NAMES = ('acrobatics', 'animalHandling', 'arcana', 'athletics', 'deception', 'history', 'initiative', 'insight',
               'intimidation', 'investigation', 'medicine', 'nature', 'perception', 'performance', 'persuasion',
               'religion', 'sleightOfHand', 'stealth', 'survival', 'strength', 'dexterity', 'constitution',
               'intelligence', 'wisdom', 'charisma')
ATTACK_RE = re.compile(r'(?:<i>)?(?:\w+ ){1,4}Attack:(?:</i>)? ([+-]?\d+) to hit, .*?(?:<i>)?'
                       r'Hit:(?:</i>)? (?:(?:[+-]?\d+ \((.+?)\))|(?:([+-]?\d+))) (\w+) damage[., ]??'
                       r'(?:in melee, or [+-]?\d+ \((.+?)\) (\w+) damage at range[,.]?)?'
                       r'(?: or [+-]?\d+ \((.+?)\) (\w+) damage (?:\w+ ?)+[.,]?)?'
                       r'(?: ?plus [+-]?\d+ \((.+?)\) (\w+) damage)?', re.IGNORECASE)
JUST_DAMAGE_RE = re.compile(r'[+-]?\d+ \((.+?)\) (\w+) damage', re.IGNORECASE)


def parse_condition(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        condition = {
            "name": raw['name'],
            "text": render(raw['entries']),
            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        out.append(condition)
    return out


def parse_disease(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        disease = {
            "name": raw['name'],
            "text": render(raw['entries']),
            "source": raw['source'],
            "page": raw.get('page', '?')
        }
        out.append(disease)
    return out


def moneyfilter(data):
    return [i for i in data if not i.get('type') == "$"]


def render_variant_eqs(entries, inherits):
    for i, entry in enumerate(entries):
        if isinstance(entry, str):
            entries[i] = re.sub(r"{=(\w+)}", lambda m: inherits.get(m.group(1), m.group(0)), entry)
        else:
            entries[i] = render(entry)
    return entries


def variant_inheritance(data):
    for item in data:
        log.debug(item['name'])
        if item.get('type') == 'GV':
            if item.get('inherits') is not None:
                if 'entries' in item['inherits']:
                    item['inherits']['entries'] = render_variant_eqs(item['inherits']['entries'], item['inherits'])
                if 'entries' in item:
                    oldentries = item['entries'].copy()
                    item.update(item['inherits'])
                    item['entries'] = oldentries
                else:
                     item.update(item['inherits'])
                del item['inherits']  # avrae doesn't parse it anyway
    return data


def prerender(data):
    for item in data:
        if 'entries' in item:
            item['desc'] = render(item['entries'])
            del item['entries']
        else:
            item['desc'] = ""

        # if 'additionalEntries' in item:
        #     item['desc'] += f"\n\n{render(item['additionalEntries'])}"
        item['desc'] = item['desc'].strip()

        for k, v in item.items():
            item[k] = recursive_tag(v)
    return data


def parse_ac(data):
    for monster in data:
        log.info(f"Parsing {monster['name']} AC")
        if isinstance(monster['ac'], dict):
            if monster['ac'].get('special', None) is not None:
                monster['ac'] = {'ac': monster['ac'].get('special')}
            else:
                monster['ac'] = {'ac': int(monster['ac']['ac']), 'armortype': render(monster['ac'].get('from', []), join_char=', ')}
        elif isinstance(monster['ac'][0], int):
            monster['ac'] = {'ac': int(monster['ac'][0])}
        elif isinstance(monster['ac'][0], dict):
            if monster['ac'][0].get('special', None) is not None:
                monster['ac'] = {'ac': monster['ac'][0].get('special')}
            else:
                monster['ac'] = {'ac': int(monster['ac'][0]['ac']), 'armortype': render(monster['ac'][0].get('from', []), join_char=', ')}
        else:
            log.warning(f"Unknown AC type: {monster['ac']}")
            raise Exception
    return data


def translate_skills(data):
    for monster in data:
        log.info(f"Parsing {monster['name']} skills")
        saves = monster.get('save', {})
        skills = monster.get('skill', {})

        new_saves = {}
        new_skills = {}

        print(saves)
        for k, v in saves.items():
            new_k = {"str": "strengthSave", "dex": "dexteritySave", "con": "constitutionSave",
                     "int": "intelligenceSave", "wis": "wisdomSave", "cha": "charismaSave", "special": "special"}[k]
            try:
                new_saves[new_k] = int(v)
            except ValueError:
                new_saves[new_k] = v

        for k, v in skills.items():
            if k not in SKILL_NAMES:
                continue
            new_k = re.sub(r"\s+(\w)", lambda m: m.group(1).upper(), k.lower())  # spaced to upper
            try:
                new_skills[new_k] = int(v)
            except ValueError:
                new_skills[new_k] = v

        monster['save'] = new_saves
        monster['skill'] = new_skills
    return data


def parse_spellcasting(monster):
    if 'trait' not in monster:
        monster['trait'] = []
    known_spells = []
    usual_dc = (0, 0)  # dc, number of spells using dc
    usual_sab = (0, 0)  # same thing
    caster_level = 1
    if monster['spellcasting'] is not None:
        hidden = []
        for cast_type in monster['spellcasting']:
            if 'hidden' in cast_type:
                for hide in cast_type['hidden']:
                    hidden.append(hide)
            if cast_type == "spells":
                return
            entries = cast_type['headerEntries'] if cast_type.get('headerEntries') is not None else cast_type['footerEntries']
            if cast_type.get('footerEntries') is not None:
                print(f"--------------------------{monster['name']}--------------------------")
            trait = {'name': cast_type['name'], 'entries': render(entries)}
            type_dc = re.search(r'\(spell save {@dc (\d+)', '\n'.join(entries))
            type_sab = re.search(r'{@?hit (\d+)}', '\n'.join(entries))
            type_caster_level = re.search(r'(\d+)[stndrh]{2}-level', '\n'.join(entries))
            type_spells = []
            if 'will' in cast_type and 'will' not in hidden:
                spells = []
                type_spells.extend(extract_spell(s) for s in cast_type['will'])
                for spell in cast_type['will']:
                    spells = parseAtWillOrDailySpells(spell, spells, monster['name'])
                spellString = ""
                for x in spells:
                    spellString += f" - {x}\n"
                trait['entries'] += f"\nAt will:\n{spellString}"
            if 'daily' in cast_type and 'daily' not in hidden:
                for times_per_day, spells in cast_type['daily'].items():
                    spellList = []
                    each = ' each' if times_per_day.endswith('e') else ''
                    times_per_day = times_per_day.rstrip('e')
                    type_spells.extend(extract_spell(s) for s in spells)
                    for spell in spells:
                        spellList = parseAtWillOrDailySpells(spell, spellList, monster['name'])
                    spellString = ""
                    for x in spellList:
                        spellString += f"- {x}\n"
                    trait['entries'] += f"\n{times_per_day}/day{each}:\n{spellString}"
            if 'spells' in cast_type and 'spells' not in hidden:
                valid_levels = map(str, range(10))
                for level, level_data in cast_type['spells'].items():
                    if level not in valid_levels:
                        continue
                    spells = level_data['spells']
                    level_text = get_spell_level(level)
                    slots = f"{level_data.get('slots', 'unknown')} slots" if level != '0' else "at will"
                    type_spells.extend(extract_spell(s) for s in spells)
                    spells = render(', '.join(spells))
                    trait['entries'] += f"\n{level_text} ({slots}): {spells}"
            trait['entries'] = render(trait['entries'])
            monster['trait'].append(trait)
            known_spells.extend(type_spells)
            if type_dc and (len(type_spells) > usual_dc[1] or not usual_dc[0]):
                usual_dc = (int(type_dc.group(1)), len(type_spells))
            if type_sab and (len(type_spells) > usual_sab[1] or not usual_sab[0]):
                usual_sab = (int(type_sab.group(1)), len(type_spells))
            if type_caster_level:
                caster_level = int(type_caster_level.group(1))
    dc = usual_dc[0]
    sab = usual_sab[0]
    monster['spellcasting'] = {'spells': known_spells, 'dc': dc, 'attackBonus': sab,
                               'casterLevel': caster_level}  # overwrite old
    # log.info(f"Lvl {caster_level}; DC: {dc}; SAB: {sab}; Spells: {known_spells}")


def parseAtWillOrDailySpells(spell, spells, name = ""):
    if isinstance(spell, dict):
        if spell.get('entry', None) is None:
            spells.append(render(spell))
        else:
            if spell.get('hidden', False) is False:
                spells.append(render(spell['entry']))
    else:
        spells.append(render(spell, name=name))
        if name == "Korred":
            print(f"KORRED - POST PARSE CURRENT SPELLS: {spells}")
    return spells


def monster_render(data):
    for monster in data:
        # log.info(f"Rendering {monster['name']}")
        for t in ('trait', 'action', 'reaction', 'legendary'):
            # log.info(f"  Rendering {t}s")
            if t in monster:
                temp = []
                try:
                    for entry in monster[t]:
                        if entry.get('entries') is not None:
                            text = render(entry['entries'])
                        else:
                            text = entry['text']
                        temp.append({'name': entry.get('name', ''), 'text': text})
                except TypeError as e:
                    log.warning(f"{monster['name']} has an empty {t}")
        if 'spellcasting' in monster:
            parse_spellcasting(monster)
    return data


def extract_spell(text):
    # TODO add support for "ethereal jaunt" Tome of Beasts.json
    try:
        return re.match(r'{@spell (.*)}', text).group(1)
    except:
        try:
            return re.match(r'{@optfeature (.*)}', text).group(1)
        except:
            return text


def get_spell_level(level):
    if level == '0':
        return "Cantrips"
    if level == '1':
        return "1st level"
    if level == '2':
        return "2nd level"
    if level == '3':
        return "3rd level"
    return f"{level}th level"


def parse_attacks(data):
    for monster in data:
        attacks = []
        for t in ('trait', 'action', 'reaction', 'legendary'):
            if t in monster:
                if monster[t] is not None:
                    for entry in monster[t]:
                        try:
                            name = entry['name']
                        except KeyError as e:
                            continue

                        try:
                            raw = entry['text']
                        except KeyError:
                            raw = entry['entries'][0]

                        if isinstance(raw,dict):
                            continue
                        raw_atks = list(ATTACK_RE.finditer(raw))
                        raw_damage = list(JUST_DAMAGE_RE.finditer(raw))

                        if raw_atks:
                            for atk in raw_atks:
                                if atk.group(7) and atk.group(8):  # versatile
                                    damage = f"{atk.group(7)}[{atk.group(8)}]"
                                    if atk.group(9) and atk.group(10):  # bonus damage
                                        damage += f"+{atk.group(9)}[{atk.group(10)}]"
                                    attacks.append(
                                        {'name': f"2 Handed {name}", 'attackBonus': atk.group(1).lstrip('+'),
                                         'damage': damage,
                                         'details': raw})
                                if atk.group(5) and atk.group(6):  # ranged
                                    damage = f"{atk.group(5)}[{atk.group(6)}]"
                                    if atk.group(9) and atk.group(10):  # bonus damage
                                        damage += f"+{atk.group(9)}[{atk.group(10)}]"
                                    attacks.append(
                                        {'name': f"Ranged {name}", 'attackBonus': atk.group(1).lstrip('+'),
                                         'damage': damage,
                                         'details': raw})
                                damage = f"{atk.group(2) or atk.group(3)}[{atk.group(4)}]"
                                if atk.group(9) and atk.group(10):  # bonus damage
                                    damage += f"+{atk.group(9)}[{atk.group(10)}]"
                                attacks.append(
                                    {'name': name, 'attackBonus': atk.group(1).lstrip('+'), 'damage': damage,
                                     'details': raw})
                        else:
                            index = 1
                            for dmg in raw_damage:
                                damage = f"{dmg.group(1)}[{dmg.group(2)}]"
                                if index > 1:
                                    name = f"{name} {index}"
                                atk = {'name': name, 'attackBonus': None, 'damage': damage, 'details': raw}
                                attacks.append(atk)
                                index += 1

        for attack in attacks:
            attack['name'] = re.sub(r"(.+)\(.+\)", r"\1", attack['name']).strip()
        monster['attacks'] = attacks
        log.debug(f"Parsed attacks for {monster['name']}: {attacks}")
    return data
