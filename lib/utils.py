import difflib
import json
import logging
import os
import re

import sys

import motor.motor_asyncio
import requests
from environs import Env
import cloudscraper

from lib.markdown import spellMarkdown, deityMarkdown

env = Env()
env.read_env()

DATA_SRC = env('DATA_SRC')
LOGLEVEL = logging.INFO if "debug" not in sys.argv else logging.DEBUG

log_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(LOGLEVEL)
logger.addHandler(handler)
log = logging.getLogger(__name__)

# MDB = motor.motor_asyncio.AsyncIOMotorClient(env('MONGODB'))['lookup']  # Server
# MDB = motor.motor_asyncio.AsyncIOMotorClient(env('MONGODB_LOCAL'))['lookup'] # Local
MDB = None

skip = ['class-rune-scribe.json', 'class-sidekick.json', 'class-generic.json']


def get_json(path):
    log.info(f"Getting {path}...")
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    try:
        resp = scraper.get(DATA_SRC + path)
        resp.raise_for_status()
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_data(path):
    dat = get_json(path)
    return dat


def get_indexed_data(root, root_key, fluff=False):
    if fluff:
        index = get_json(f'{root}fluff-index.json')
    else:
        index = get_json(f'{root}index.json')
    out = []
    for src, file in index.items():
        # if file in ["fluff-bestiary-lmop.json"]:
        if file not in skip:
            if '3pp' in src or 'Stream' in src:
                log.info(f"Skipped {file}: {src}")
                continue
            data = get_json(f"{root}{file}")
            out.extend(data[root_key])
            log.info(f"\tProcessed {file}: {len(data[root_key])} entries")
    return out


def get_indexed_datas(root, root_keys):
    index = get_json(f'{root}index.json')
    clazz = []
    cfeats = []
    sfeats = []
    for src, file in index.items():
        if file not in skip:
            if '3pp' in src or 'Stream' in src:
                log.info(f"Skipped {file}: {src}")
                continue
            data = get_json(f"{root}{file}")
            for x in root_keys:
                if x == "class":
                    if data.get(x) is not None:
                        if not data.get(x) in skip:
                            for claz in data[x]:
                                if claz['source'] not in skip:
                                    clazz.extend([claz])
                            log.info(f"  Processed {file}: {len(data[x])} class entries")
                if x == "subclass":
                    if data.get(x) is not None:
                        item = [item for item in clazz if item["name"].lower() == src.lower() and ('UA' not in item['source'] or item["name"].lower() == "mystic")][0]
                        item.update({"subclasses": data[x]})
                        log.info(f"  Processed {file}: {len(data[x])} subclass entries")
                if x == "classFeature":
                    if data.get(x) is not None:
                        cfeats.extend(data[x])
                        log.info(f"  Processed {file}: {len(data[x])} class feature entries")
                if x == "subclassFeature":
                    if data.get(x) is not None:
                        sfeats.extend(data[x])
                        log.info(f"  Processed {file}: {len(data[x])} subclass feature entries")
    return clazz, cfeats, sfeats


async def dump(data, filename, MDB=MDB, md=False):
    updated = 0
    inserted = 0
    try:
        os.rename(f'./out/{filename}', f'./bak/{filename}.old')
    except FileNotFoundError:
        pass
    with open(f'./out/{filename}', 'w') as f:
        json.dump(data, f, indent=2)
    length = len(data)
    actual = 0
    print("Upserting Data")
    printProgressBar(0, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
    for i, x in enumerate(data):
        actual += 1
        if md:
            path = f'./markdown/{filename[:-5]}/'
            if not os.path.exists(path):
                os.makedirs(path)
            with open(f"{path}{x['name'].replace('/',' ')}.md", 'w') as f:
                if filename[:-5] == "spells":
                    spellMarkdown(x, f)
                if filename[:-5] == "deities":
                    deityMarkdown(x, f)
                if (i % 10) == 0:
                    printProgressBar(i + 1, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
        else:
            collection = MDB[f'{filename[:-5]}']
            found = await collection.find_one({"name": x['name']})
            if found is not None:
                await collection.replace_one({"name": x['name']}, x)
                updated = updated + 1
                if (i % 10) == 0:
                    printProgressBar(i + 1, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
            else:
                await collection.insert_one(x)
                inserted = inserted + 1
                if (i % 10) == 0:
                    printProgressBar(i + 1, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
    printProgressBar(length, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
    print(f"\nInserted: {inserted}")
    print(f"\nUpdated: {updated}")


async def dump_classfeats(data, filename, MDB=MDB):
    inserted = 0
    try:
        os.rename(f'./out/{filename}', f'./bak/{filename}.old')
    except FileNotFoundError:
        pass
    with open(f'./out/{filename}', 'w') as f:
        json.dump(data, f, indent=2)
    collection = MDB[f'{filename[:-5]}']
    await collection.delete_many({})
    length = len(data)
    actual = 0
    printProgressBar(0, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
    for i, x in enumerate(data):
        await collection.insert_one(x)
        actual += 1
        inserted = inserted + 1
        if (i % 10) == 0:
            printProgressBar(i + 1, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)

    printProgressBar(length, length, prefix='Upserting Data:', suffix=f'Complete ({actual}/{length})', length=50)
    print(f"Inserted: {inserted}")


def diff(filename):
    try:
        with open(f'./bak/{filename}.old') as before:
            old = before.readlines()
        with open(f'./out/{filename}') as after:
            new = after.readlines()
    except FileNotFoundError:
        return
    sys.stdout.writelines(difflib.unified_diff(old, new, fromfile=f"./bak/{filename}.old", tofile=f"./out/{filename}"))


def nth_repl(s, sub, repl, nth):
    find = s.find(sub)
    # if find is not p1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != nth:
        # find + 1 means we start at the last match start index + 1
        find = s.find(sub, find + 1)
        i += 1
    # if i  is equal to nth we found nth matches so replace
    if i == nth:
        return s[:find] + repl + s[find + len(sub):]
    return s


def explicit_sources(data, sources):
    for entry in data:
        if entry['source'] in sources:
            new_name = f"{entry['name']} ({entry['source']})"
            log.info(f"Renaming {entry['name']} to {new_name} (explicit override)")
            entry['name'] = new_name
    return data


def fix_dupes(data, source_hierarchy, remove_dupes=False):
    for entry in data.copy():
        if len([r for r in data if r['name'] == entry['name']]) > 1:
            log.warning(f"Found duplicate: {entry['name']}")
            hierarchied = sorted([r for r in data if r['name'] == entry['name']],
                                 key=lambda r: source_hierarchy.index(
                                     next((s for s in source_hierarchy if s in r['source']), 'nil')))
            for r in hierarchied[1:]:
                if not remove_dupes:
                    new_name = f"{r['name']} ({r['source']})"
                    log.info(f"Renaming {r['name']} to {new_name}")
                    r['name'] = new_name
                else:
                    log.info(f"Removing {r['name']} ({r['source']})")
                    data.remove(r)
    return data


def remove_ignored(data, ignored_sources, subclass=False):
    for entry in data.copy():
        if entry['source'] in ignored_sources:
            data.remove(entry)
            log.info(f"{entry['name']} ({entry['source']}) ignored, removing!")
        if subclass:
            if entry['classSource'] in ignored_sources:
                if entry in data:
                    data.remove(entry)
                log.info(f"{entry['name']} ({entry['classSource']}) ignored, removing!")
        else:
            print(entry['name'])
    return data


def camel_to_title(string):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', string).title()


def english_join(l):
    l = list(l)
    if len(l) < 2:
        return l[0]
    elif len(l) == 2:
        return ' or '.join(l)
    else:
        return ', '.join(l[:-1]) + f', or {l[-1]}'


def srdonly(data):
    return [b for b in data if b['srd']]


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    complete = f'{prefix} |{bar}| {percent}% {suffix}'

    print(complete, flush=True)

    # Print New Line on Complete
    if iteration == total:
        print()