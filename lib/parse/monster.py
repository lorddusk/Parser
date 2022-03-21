import json

import motor.motor_asyncio
from environs import Env
from lib import logger

env = Env()
env.read_env()

IGNORED = ['Sample - Giddy', '_generated', '_img', '_node', 'package-lock', 'package', 'schema']

log = logger.logger

lookup = motor.motor_asyncio.AsyncIOMotorClient(env('MONGODB_LOCAL'))['lookup']

async def parseMonsterCopies(data):
    for i, monster in enumerate(data):
        if '_copy' not in monster:
            continue
        original = monster.copy()  # how ironic
        del original['_copy']

        copymeta = monster['_copy']
        log.info(f"Copying {copymeta['name']} onto {monster['name']}...")
        # to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])
        to_copy = await lookup.bestiary.find_one({"name": f"{copymeta['name']}", "source": f"{copymeta['source']}"})

        # I hate this so much
        to_copy.pop('_id')
        data_str = json.dumps(to_copy)
        for replacer in copymeta.get('replacers', []):
            data_str = data_str.replace(replacer['replace'], replacer['with'])
        copied = json.loads(data_str)

        for key, mod in copymeta.get('arrayModifiers', {}).items():
            for action in mod:
                if action['mode'] == 'replace':
                    for entry in action['data']:
                        to_replace = next(e for e in copied[key] if e['name'] == entry['replace'])
                        entry.pop('replace')
                        to_replace.update(entry)
                elif action['mode'] == 'remove':
                    if 'data' not in action:
                        try:
                            del copied[key]
                        except KeyError:
                            log.warning(f"I tried to delete key {key} but it does not exist")
                            continue
                    else:
                        for to_remove in action['data']:
                            try:
                                copied[key].remove(next(e for e in copied[key] if e['name'] == to_remove['remove']))
                            except StopIteration:
                                log.warning(f"I tried to remove {key}.{to_remove['remove']} but it does not exist")
                                continue
                elif action['mode'] == 'prepend':
                    for entry in reversed(action['data']):
                        copied[key].insert(0, entry)
                elif action['mode'] == 'append':
                    copied[key].extend(action['data'])
                else:
                    log.warning(f"Unknown copy action: {action['mode']}")

        copied.update(original)
        data[i] = copied
    return data