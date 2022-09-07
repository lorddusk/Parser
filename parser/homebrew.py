import asyncio
import sys
import traceback
from pathlib import Path
import json
import lib.parsingmethods as pm
from lib.parse.backgrounds import parseBackgrounds, srdfilter
from lib.parse.race import parseRaceCopies, splitSubraces
from lib.parse.deity import parseDeity, deitySrdFilter
from lib.parse.feats import parseFeats
from lib.parse.monster import parseMonsterCopies
from lib.utils import dump
from lib.parse.spells import parseSpells
import motor.motor_asyncio
from environs import Env
from lib import logger

env = Env()
env.read_env()

MDB = motor.motor_asyncio.AsyncIOMotorClient(env('MONGODB'))['homebrew']
# MDB = motor.motor_asyncio.AsyncIOMotorClient(env('MONGODB_LOCAL'))['homebrew']


IGNORED = ['Sample - Giddy', '_generated', '_img', '_node', 'package-lock', 'package', 'schema']

log = logger.logger


async def run():
    file = None
    for x in Path("./in/homebrew").rglob('*.json'):
        if not any(ext in str(x) for ext in IGNORED):
            print(f"PARSING : {x}")
            path = ".\\" + str(x)
            try:
                file = json.load(open(path, "r", encoding='utf8'))
            except UnicodeDecodeError as e:
                print(e)
                continue
            for x in file:
                try:
                    unlisted = file.get("_meta").get("unlisted", False)
                    if unlisted:
                        print("UNLISTED BITCHES")
                        break
                    if x == "race":
                        data = parseRaceCopies(file['race'])
                        data = splitSubraces(data)
                        data = srdfilter(data)
                        await dump(data, 'races.json', MDB)
                    if x == "deity":
                        data = parseDeity(file['deity'])
                        data = deitySrdFilter(data)
                        await dump(data, 'deities.json', MDB)
                    if x == "background":
                        data = parseBackgrounds(file['background'])
                        data = srdfilter(data)
                        await dump(data, 'backgrounds.json', MDB)
                    if x == "feat":
                        data = parseFeats(file['feat'])
                        await dump(data, 'feats.json', MDB)
                    if x == "spell":
                        data = parseSpells(file['spell'])
                        await dump(data, 'spells.json', MDB)
                    if x == "condition":
                        data = pm.parse_condition(file["condition"])
                        await dump(data, 'conditions.json', MDB)
                    if x == "disease":
                        data = pm.parse_disease(file["disease"])
                        await dump(data, 'diseases.json', MDB)
                    if x == "item":
                        data = pm.moneyfilter(file["item"])
                        data = pm.variant_inheritance(data)
                        data = pm.prerender(data)
                        await dump(data, 'items.json', MDB)
                    if x == "monster":
                        data = await parseMonsterCopies(file['monster'])
                        data = pm.parse_ac(data)
                        data = pm.translate_skills(data)
                        rendered = pm.monster_render(data)
                        rendered = pm.recursive_tag(rendered)
                        out = pm.parse_attacks(rendered)
                        await dump(out, 'bestiary.json', MDB)
                except Exception as e:
                    exc_info = sys.exc_info()
                    file = open(f'./logs/homebrewTrace.log', 'a')
                    fileErrors = open(f'./logs/HPFN.log', 'a')
                    fileName = path.split('\\')[-1]
                    fileType = path.split('\\')[-2]
                    print(f"ERROR IN {fileType}\{fileName}")
                    file.write(f"ERROR IN {fileType}\{fileName} - TYPE: {str(e)}\n")
                    fileErrors.write(f"ERROR IN {fileType}\{fileName} - TYPE: {str(e)}\n")
                    traceback.print_exception(*exc_info, file=file)
                    traceback.print_exception(*exc_info)
                    file.write(f"\n\n")
                    file.close()
                    fileErrors.close()
                    del exc_info
                    break


async def parseMeta(file):
    data = file['_meta']
    sources = data['sources']
    for x in sources:
        abr = x['abbreviation']
        full = x['full']
        version = x['version']
        source = x.get('url','n/a')

        hb = {
            "name": full,
            "abbreviation": abr,
            "version": version,
            "source": source
        }
        # collection = MDB[f'homebrewSource']
        # found = await collection.find_one({"name": hb['name']})
        # if found is not None:
        #     await collection.replace_one({"name": hb['name']}, hb)
        # else:
        #     await collection.insert_one(hb)


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
