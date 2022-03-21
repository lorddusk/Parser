import logging
import copy
import json

from lib.copy import checkCopyMeta

log = logging.getLogger("races")

def splitSubraces(races):
    out = []
    for race in races:
        log.info(f"Processing race {race['name']}")
        if 'subraces' not in race:
            out.append(race)
        else:
            subraces = race['subraces']
            del race['subraces']
            for subrace in subraces:
                if subrace.get('name', None) is not None:
                    log.info(f"Processing subrace {subrace.get('name')}")
                else:
                    log.info(f"Processing base subrace")
                new = copy.deepcopy(race)
                if 'name' in subrace:
                    new['name'] = f"{race['name']} ({subrace['name']})"
                if 'ability' in subrace:
                    if 'ability' in new:
                        new['ability'] = new['ability'] + subrace['ability']
                    else:
                        new['ability'] = subrace['ability']
                if 'speed' in subrace:
                    new['speed'] = subrace['speed']
                if 'source' in subrace:
                    new['source'] = subrace['source']
                if 'overwrite' in subrace:
                    if subrace['overwrite'].get('ability') is not None:
                        new['ability'] = subrace['ability']
                    if subrace['overwrite'].get('languageProficiencies') is not None:
                        new['languageProficiencies'] = subrace['languageProficiencies']
                    if subrace['overwrite'].get('skillProficiencies') is not None:
                        new['skillProficiencies'] = subrace['skillProficiencies']
                    if subrace['overwrite'].get('ability') is not None:
                        new['ability'] = subrace['ability']
                    if subrace['overwrite'].get('traitTags') is not None:
                        if new.get('traitTags') is not None:
                            if subrace.get('traitTags') is None:
                                new['traitTags'] = None
                            else:
                                new['traitTags'] = subrace['traitTags']
                if 'entries' in subrace:
                    for x in subrace['entries']:
                        if 'data' in x:
                            overwrite = x['data']['overwrite']
                            for y in new['entries']:
                                if y.get('name') == overwrite:
                                    new['entries'].remove(y)
                                    new['entries'].append(x)
                        else:
                            new['entries'].append(x)

                out.append(new)
    return out


def parseRaceCopies(data):
    for i, items in enumerate(data):
        if '_copy' not in items:
            continue
        original = items.copy()  # how ironic
        del original['_copy']

        copymeta = items['_copy']
        log.info(f"Copying {copymeta['name']} onto {items['name']}...")
        to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])

        if to_copy.get('subraces'):
            del to_copy['subraces']

        data_str = json.dumps(to_copy)
        if copymeta.get('_mod', None) is not None:
            for key, mods in copymeta.get('_mod', []).items():
                data_str = checkCopyMeta(data_str, key, mods)

        copied = json.loads(data_str)

        copied.update(original)
        data[i] = copied
    return data