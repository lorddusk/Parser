import logging
import re
import typing
import textwrap
from lib.parse.clazz import *

log = logging.getLogger(__name__)

ABILITY_MAP = {'str': 'Strength', 'dex': 'Dexterity', 'con': 'Constitution',
               'int': 'Intelligence', 'wis': 'Wisdom', 'cha': 'Charisma'}
ATTACK_TYPES = {"M": "Melee", "R": "Ranged", "W": "Weapon", "S": "Spell"}


def render(text, md_breaks=False, join_char='\n', _class=None, subclass=None, options=None, name=""):
    """Parses a list or string from data.
    :returns str - The final text."""
    if isinstance(text, dict):
        text = [text]
    if not isinstance(text, list):
        return parse_data_formatting(str(text))

    out = []
    join_str = f'{join_char}' if not md_breaks else f'  {join_char}'

    for entry in text:
        if not isinstance(entry, dict):
            out.append(str(entry))
        elif isinstance(entry, dict):
            if 'type' not in entry and 'title' in entry:
                out.append(f"**{entry['title']}**: {render(entry['text'], _class=_class, subclass=subclass, options=options)}")

            elif 'type' not in entry and 'istable' in entry:  # only for races
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else ''
                temp += ' - '.join(f"**{parse_data_formatting(cl)}**" for cl in entry['thead']) + '\n'
                for row in entry['tbody']:
                    temp += ' - '.join(f"{parse_data_formatting(col)}" for col in row) + '\n'
                out.append(temp.strip())

            elif 'type' not in entry or entry['type'] in ('entries', 'inset', 'insetReadaloud'):
                if 'entry' in entry:
                    out.append(entry['entry'])
                else:
                    out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))  # oh gods here we goooooooo

            elif entry['type'] == 'options':
                classOptions = [e for e in entry['entries'] if isinstance(e, dict)]
                for option in classOptions:
                    # log.info(f"Found option for feature below")
                    out.append(render(option, _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'list':
                out.append('\n'.join(f"- {render(t, _class=_class, subclass=subclass, options=options)}" for t in entry['items']))

            elif entry['type'] == 'table':
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else '\n'
                # temp += render_table(entry)
                temp += ' - '.join(f"**{parse_data_formatting(cl)}**" for cl in entry['colLabels']) if 'colLabels' in entry else '' + '\n'
                temp += '\n'
                for row in entry['rows']:
                    temp += ' - '.join(f"{render(col, _class=_class, subclass=subclass, options=options)}" for col in row) + '\n'
                out.append(temp.strip())

            elif entry['type'] == 'invocation':
                pass  # this is only found in options

            elif entry['type'] == 'abilityAttackMod':
                out.append(f"`{entry['name']} Attack Bonus = "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")

            elif entry['type'] == 'abilityDc':
                out.append(f"`{entry['name']} Save DC = 8 + "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")

            elif entry['type'] == 'bonus':
                out.append("{:+}".format(entry['value']))

            elif entry['type'] == 'dice':
                out.append(f"{entry['number']}d{entry['faces']}")

            elif entry['type'] == 'bonusSpeed':
                out.append(f"{entry['value']} feet")

            elif entry['type'] == 'actions':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'attack':
                out.append(f"{' '.join(ATTACK_TYPES.get(t) for t in entry['attackType'])} Attack: "
                           f"{render(entry['attackEntries'], _class=_class, subclass=subclass, options=options)} Hit: {render(entry['hitEntries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'item':
                try:
                    out.append(f"*{entry['name']}* {render(entry['entry'], _class=_class, subclass=subclass, options=options)}")
                except:
                    try:
                        out.append(f"*{entry['name']}* {render(entry['entries'], _class=_class, subclass=subclass, options=options)}")
                    except:
                        pass

            elif entry['type'] == 'itemSub':
                try:
                    out.append(f"*{entry['name']}* {render(entry['entry'], _class=_class, subclass=subclass, options=options)}")
                except:
                    out.append(f"*{entry['name']}* {render(entry['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'cell':
                if 'entry' in entry:
                    out.append(render(entry['entry'], _class=_class, subclass=subclass, options=options))
                else:
                    if 'exact' in entry['roll']:
                        out.append(str(entry['roll']['exact']))
                    else:
                        out.append(f"{str(entry['roll']['min'])} - {str(entry['roll']['max'])}")

            elif entry['type'] == 'inline':
                if 'entries' in entry:
                    string = render(entry['entries'], _class=_class, subclass=subclass, options=options) + 'indefinite maddness.'
                    out.append(string.replace("\n.", ""))

            elif entry['type'] == 'abilityGeneric':
                out.append(f"`{entry['text']}`")

            elif entry['type'] == 'section':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'inlineBlock':
                out.append("At 2nd level, you gain two eldritch invocations of your choice. When you gain certain warlock levels, you gain additional invocations of your choice.")

            elif entry['type'] == 'refClassFeature':
                classfeat = entry['classFeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['classFeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getClassFeature(CreateClassSplit(feat), _class)
                out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'refSubclassFeature':
                classfeat = entry['subclassFeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['subclassFeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getSubClassFeature(CreateSubclassSplit(feat), subclass)
                out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'refOptionalfeature':
                classfeat = entry['optionalfeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['optionalfeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getOptionalFeature(feat, options)
                if feature is not None:
                    if feature.get('srd', None) is not None:
                        out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            else:
                log.warning(f"Missing data entry type parse: {entry}")

        else:
            log.warning(f"Unknown data entry: {entry}")

    return parse_data_formatting(join_str.join(out))


def SRC_FORMAT(e):
    if e is not None:
        return e.split('|')[0] if len(e.split('|')) < 3 else e.split('|')[2]
    else:
        return None


ATK_TYPES = {'mw': "Melee Weapon", 'rw': "Ranged Weapon", 'mw,rw': "Melee or Ranged Weapon",
             'ms': "Melee Spell", 'rs': "Ranged Spell", 'ms,rs': "Melee or Ranged Spell"}
FORMATTING = {'bold': '**', 'italic': '*', 'b': '**', 'i': '*'}
PARSING = {
    'adventure': lambda e: e.split('|')[0],
    'atk': lambda e: f"{ATK_TYPES.get(e, 'Unknown')} Attack:",
    'book': lambda e: e.split('|')[0],
    'chance': lambda e: e.split('|')[1] if len(e.split('|')) > 1 else f"{e.split('|')[0]}%",
    'classFeature': lambda e: e.split('|')[0],
    'd20': lambda e: f"+{e}",
    'dc': lambda e: f"DC {e}",
    'deity': lambda e: e.split('|')[0],
    'dice': lambda e: e.split('|')[-1],
    'disease': lambda e: e.split('|')[0],
    'feat': lambda e: e.split('|')[0],
    'filter': lambda e: e.split('|')[0],
    'h': lambda e: "Hit: ",
    'hazard': lambda e: e.split('|')[0],
    'hit': lambda e: f"+{e}",
    'language': lambda e: f"{e}",
    'link': lambda e: f"[{e.split('|')[0]}]({e.split('|')[1]})",
    'quickref': lambda e: e.split('|')[0],
    'recharge': lambda e: f"(Recharge {e}-6)" if e else "(Recharge 6)",
    'scaledamage': lambda e: e.split('|')[-1],
    'scaledice': lambda e: e.split('|')[-1],
    'variantrule': lambda e: e.split('|')[0],
    'optfeature': lambda e: e.split('|')[0],
    'hitYourSpellAttack': lambda e: f"your spell attack modifier"
}
DEFAULT = ['condition', 'skill', 'action', 'creature', 'item', 'spell', 'damage', 'race', 'background',
           'class', 'table', 'sense']
IGNORE = ['note', '5etools', 'area']


def parse_data_formatting(text):
    """Parses a {@format } string."""
    exp = re.compile(r'{@(\w+)(?: ([^{}]+?))?}')

    def sub(match):
        log.debug(f"Rendering {match.group(0)}...")
        if match.group(1) in FORMATTING:
            f = FORMATTING.get(match.group(1), '')
            out = f"{f}{match.group(2)}{f}"
        elif match.group(1) in PARSING:
            f = PARSING.get(match.group(1), lambda e: e)
            if f(match.group(2)) == "Starting Gold":
                out = f"{match.group(0).split('|')[1]}"
            else:
                out = f(match.group(2))
        else:
            out = SRC_FORMAT(match.group(2))
            if not match.group(1) in DEFAULT and not match.group(1) in IGNORE:
                log.warning(f"Possible unknown tag: {match.group(0)}")
        log.debug(f"Replaced with {out}")
        return out

    while exp.search(text):
        text = exp.sub(sub, text)
    return text


def recursive_tag(value):
    """
    Recursively renders all tags.
    :param value: The object to render tags from.
    :return: The object, with all tags rendered.
    """
    if isinstance(value, str):
        return render(value)
    if isinstance(value, list):
        return [recursive_tag(i) for i in value]
    if isinstance(value, dict):
        for k, v in value.items():
            value[k] = recursive_tag(v)
    return value
