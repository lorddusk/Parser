import json
import re
import math
from collections import defaultdict


skillStats = {'acrobatics': 'dex', 'animalHandling': 'wis', 'arcana': 'int', 'athletics': 'str', 'deception': 'cha',
              'history': 'int', 'insight': 'wis', 'intimidation': 'cha', 'investigation': 'int', 'medicine': 'wis',
              'nature': 'int', 'perception': 'wis', 'performance': 'cha', 'persuasion': 'cha', 'religion': 'int',
              'sleightOfHand': 'dex', 'stealth': 'dex', 'survival': 'wis'}


def regexParsing(data_str, meta, monsterName):
    data = json.loads(data_str)
    pattern = re.compile("<\\$title_name\\$>", re.IGNORECASE)
    data_str = pattern.sub(monsterName, data_str)

    pattern = re.compile("<\\$short_name\\$>", re.IGNORECASE)
    data_str = pattern.sub(meta['name'], data_str)

    pattern = re.compile("<\\$spell_dc__cha\\$>", re.IGNORECASE)
    dc = 8 + getProf(data) + getMod(data[f'cha'])
    data_str = pattern.sub(str(dc), data_str)

    pattern = re.compile("<\\$damage_mod__str\\$>", re.IGNORECASE)
    mod = getMod(data[f'str'])
    if mod > 0:
        data_str = pattern.sub(f" + {mod}", data_str)
    else:
        data_str = pattern.sub("", data_str)

    pattern = re.compile("<\\$damage_avg__2.5+str\\$>", re.IGNORECASE)
    dmg = math.floor(2.5 + getMod(data[f'str']))
    data_str = pattern.sub(str(dmg), data_str)

    pattern = re.compile("<\\$to_hit__str\\$>", re.IGNORECASE)
    toHit = getProf(data) + getMod(data[f'str'])
    data_str = pattern.sub(str(toHit), data_str)

    return data_str


def checkCopyMeta(data_str, key, mods):
    if isinstance(mods, str):
        if mods == 'remove':
            data_str = remove(data_str, key)
        elif key == "size":
            data_str = change(data_str, mods, "size")
    elif isinstance(mods, dict):
        if key == "type":
            data_str = change(data_str, mods, "type")
        elif key == "speed":
            data_str = change(data_str, mods, "speed")
    elif isinstance(mods, int):
        if key == "speed":
            data_str = change(data_str, mods, "speed")
        elif key == "int" or key == "str" or key == "wis" or key == "cha" or key == "dex" or key == "con":
            data_str = change(data_str, mods, "stat", key)

    if not isinstance(mods, str) and not isinstance(mods, int):
        for mod in mods:
            if mod == 'mode':
                if isinstance(mods, str):
                    if mod == 'remove':
                        data_str = remove(data_str, key)

                elif isinstance(mods, dict):
                    if key == "*":
                        if mods['mode'] == 'replaceTxt':
                            pattern = re.compile(mods['replace'], re.IGNORECASE)
                            data_str = pattern.sub(mods['with'], data_str)
                    elif key == "_":
                        if mods['mode'] == 'addSkills':
                            data_str = addSkills(data_str, mods)
                        elif mods['mode'] == 'addSenses':
                            data_str = addSenses(data_str, mods)
                        elif mods['mode'] == 'replaceSpells':
                            data_str = replaceSpells(data_str, mods)
                    elif mods['mode'] == 'replaceArr':
                        data_str = replaceArr(data_str, mods, key)
                    elif mods['mode'] == 'insertArr':
                        data_str = insertArr(data_str, mods, key)
                    elif mods['mode'] == 'removeArr':
                        data_str = removeArr(data_str, mods, key)
                    elif mods['mode'] == 'prependArr':
                        data_str = prependArr(data_str, mods, key)
                    elif mods['mode'] == 'appendArr':
                        data_str = appendArr(data_str, mods, key)
                    elif mods['mode'] == 'addSpells':
                        data_str = addSpells(data_str, mods)
                    elif mods['mode'] == 'replaceSpells':
                        data_str = replaceSpells(data_str, mods)
                    elif mods['mode'] == 'replaceOrAppendArr':
                        try:
                            data_str = replaceArr(data_str, mods, key)
                        except:
                            data_str = appendArr(data_str, mods, key)
                    elif mods['mode'] == 'appendIfNotExistsArr':
                        data_str = appendArr(data_str, mods, key)

                elif isinstance(mods, list):
                    if key == "*":
                        if mods[mod] == 'replaceTxt':
                            pattern = re.compile(mods['replace'], re.IGNORECASE)
                            data_str = pattern.sub(mods['with'], data_str)
                    elif key == "_":
                        print(mods)

            elif isinstance(mod, dict):
                if mod['mode'] == 'addSkills':
                    data_str = addSkills(data_str, mod)

    return data_str


def addSkills(data_str, mod):
    data = json.loads(data_str)
    skills = mod["skills"]
    for i in skills:
        bonus = getProf(data) * skills[i]
        stat = skillStats.get(i)
        stat = data[f'{stat}']
        mod = stat // 2 - 5
        toApp = {i: f'+{bonus + mod}'}
        try:
            data[f'skill'].update(toApp)
        except KeyError:
            data['skill'] = toApp
    data_str = json.dumps(data)
    return data_str


def addSenses(data_str, mod):
    data = json.loads(data_str)
    senses = mod["senses"]
    toApp = [f"{senses['type']} {senses['range']}ft."]
    data["senses"] = toApp
    data_str = json.dumps(data)
    return data_str


def getProf(data):
    cr = data['cr']
    if not isinstance(cr, str):
        if cr.get('cr', None) is not None:
            cr = cr.get('cr')
    if cr == '1/2' or cr == '1/4' or cr == '1/8':
        cr = 0
    return math.ceil(int(cr) / 4) + 1


def change(data_str, mods, _type, stat = None):
    data = json.loads(data_str)

    if _type == "size":
        data['size'] = mods
    elif _type == "speed":
        if isinstance(mods, int):
            data['speed']['walk'] = mods
        else:
            data['speed'] = mods
    elif _type == "type":
        data['type'] = mods
    elif _type == "stat":
        data[stat] = mods

    data_str = json.dumps(data)
    return data_str


def getMod(data):
    return data // 2 - 5


def addSpells(data_str, mod):
    data = json.loads(data_str)

    sp = data['spellcasting'][0]
    dd = defaultdict(list)

    if mod.get('spells', None) is not None:
        for d in (sp['spells'], mod['spells']):
            for key, value in d.items():
                if len(dd[key]) > 0:
                    dd[key][0]['spells'].extend([value][0]['spells'])
                else:
                    dd[key].append(value)
    else:
        for key, value in mod.items():
            if key != "mode":
                for d in (sp[key], value):
                    if isinstance(d, dict):
                        for keyD, valueD in d.items():
                            if len(dd[key]) > 0:
                                dd[key][0].extend(valueD)
                            else:
                                dd[key].append(valueD)
                    else:
                        d += value

    data_str = json.dumps(data)
    return data_str


def replaceSpells(data_str, mod):
    data = json.loads(data_str)

    sp = data['spellcasting'][0]
    if mod.get('spells', None) is not None:
        for key, value in mod['spells'].items():
            rp = value[0]['replace']
            replaceWith = value[0]['with']
            sp['spells'][key]['spells'] = [w.replace(rp, replaceWith) for w in sp['spells'][key]['spells']]
    else:
        for key, value in mod.items():
            if key != "mode":
                for keyD, valueD in value.items():
                    rp = valueD[0]['replace']
                    replaceWith = valueD[0]['with']
                    sp[key][keyD] = [w.replace(rp, replaceWith) for w in sp[key][keyD]]
    data_str = json.dumps(data)
    return data_str


def prependArr(data_str, mods, key):
    data = json.loads(data_str)

    try:
        data[f'{key}'].update(mods['items'])
    except KeyError:
        array = [mods['items']]
        data.update({f'{key}': array})
    except AttributeError:
        if isinstance(mods['items'], list):
            array = mods['items']
        else:
            array = [mods['items']]
        data[f'{key}'] += array

    data_str = json.dumps(data)
    return data_str


def insertArr(data_str, mods, key):
    data = json.loads(data_str)

    data[f'{key}'].insert(mods['index'], mods['items'])

    data_str = json.dumps(data)
    return data_str


def replaceArr(data_str, mods, key):
    data = json.loads(data_str)
    toReplace = mods['replace']

    currActions = data[f'{key}']
    if isinstance(mods['items'], list):
        if len(mods['items']) > 1:
            for i in range(0, len(mods['items'])):
                currActions.insert(i, {'name': mods['items'][i]['name'], 'entries': mods['items'][i]['entries']})
                for x in range(len(currActions)):
                    if currActions[x]['name'] == toReplace:
                        del currActions[x]
                        break
    else:
        for x in currActions:
            try:
                if x['name'] == toReplace:
                    x['name'] = mods['items']['name']
                    x['entries'] = mods['items']['entries']
            except:
                pass

    data_str = json.dumps(data)
    return data_str


def appendArr(data_str, mods, key):
    data = json.loads(data_str)
    try:
        append = data[f'{key}']
    except:
        data[f'{key}'] = []
        append = data[f'{key}']
    items = mods['items']

    if isinstance(items, list):
        for x in items:
            append.append(x)

    if isinstance(items, dict):
        if items.get('type', None) is not None:
            items.pop('type')
        append.append(items)
        try:
            data.update(append)
        except ValueError:
            pass

    if isinstance(items, str):
        append.append(items)

    data_str = json.dumps(data)
    return data_str


def removeArr(data_str, mods, key):
    data = json.loads(data_str)

    if mods.get('names', None) is not None:
        data[f'{key}'].remove(next(e for e in data[f'{key}'] if e['name'] in mods['names']))
    if mods.get('items', None) is not None:
        data[f'{key}'].remove(mods['items'])

    data_str = json.dumps(data)
    return data_str


def remove(data_str, key):
    data = json.loads(data_str)
    data.pop(key)
    data_str = json.dumps(data)
    return data_str