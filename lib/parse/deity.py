import asyncio
import json
import logging

from lib.copy import checkCopyMeta
from lib.parsing import render
from lib.utils import dump, get_data, fix_dupes

log = logging.getLogger("deities")

SOURCE_HIERARCHY = ('MTF', 'VGM', 'GGR', 'SCAG', 'DMG', 'UA', 'nil')


def parseDeity(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        if raw.get('title') is not None and raw.get('symbol') is None:
            deity = {"name": raw['name'],
                     "alignment": alignment(raw['alignment'] if raw.get('alignment') is not None else "None"),
                     "title": raw['title'],
                     "pantheon": raw['pantheon'],
                     "domains": domains(raw['domains'] if raw.get('domains') is not None else "None"),
                     "symbol": '?',
                     "source": raw['source'],
                     "page": raw.get('page', '?'),
                     "text": render(raw['entries'] if raw.get('entries') is not None else "")
                     }
            out.append(deity)
        elif raw.get('title') is not None:
            deity = {"name": raw['name'],
                     "alignment": alignment(raw['alignment'] if raw.get('alignment') is not None else "None"),
                     "title": raw['title'],
                     "pantheon": raw['pantheon'],
                     "domains": domains(raw['domains'] if raw.get('domains') is not None else "None"),
                     "symbol": raw['symbol'],
                     "source": raw['source'],
                     "page": raw.get('page', '?'),
                     "text": render(raw['entries'] if raw.get('entries') is not None else "")
                     }
            out.append(deity)
        elif raw.get('province') is not None and raw.get('category') is not None:
            deity = {"name": raw['name'],
                     "alignment": alignment(raw['alignment'] if raw.get('alignment') is not None else "None"),
                     "province": raw['province'],
                     "category": raw['category'],
                     "pantheon": raw['pantheon'],
                     "domains": domains(raw['domains'] if raw.get('domains') is not None else "None"),
                     "symbol": raw['symbol'] if raw.get('symbol') is not None else "",
                     "source": raw['source'],
                     "page": raw.get('page', '?'),
                     "text": render(raw['entries'] if raw.get('entries') is not None else "")
                     }
            out.append(deity)
        elif raw.get('province') is not None:
            deity = {"name": raw['name'],
                     "alignment": alignment(raw['alignment'] if raw.get('alignment') is not None else "None"),
                     "province": raw['province'],
                     "pantheon": raw['pantheon'],
                     "domains": domains(raw['domains'] if raw.get('domains') is not None else "None"),
                     "symbol": raw['symbol'],
                     "source": raw['source'],
                     "page": raw.get('page', '?'),
                     "text": render(raw['entries'] if raw.get('entries') is not None else "")
                     }
            out.append(deity)
    return out


def alignment(data):
    out = []
    if data != "None":
        for x in data:
            out.append(x)
    else:
        out.append(data)
    return out


def domains(data):
    out = []
    for x in data:
        out.append(x)
    return out


def deitySrdFilter(data):
    with open('./srd/srd-deities.txt') as f:
        srd = [s.strip().lower() for s in f.read().split('\n')]
    for monster in data:
        if monster['name'].lower() in srd:
            monster['srd'] = True
        else:
            monster['srd'] = False
    return data


def parseDeityCopies(data):
    for i, deity in enumerate(data):
        if '_copy' not in deity:
            continue
        original = deity.copy()  # how ironic
        del original['_copy']

        copymeta = deity['_copy']
        log.info(f"Copying {copymeta['name']} onto {deity['name']}...")
        to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])

        data_str = json.dumps(to_copy)
        if copymeta.get('_mod', None) is not None:
            for key, mods in copymeta.get('_mod', []).items():
                data_str = checkCopyMeta(data_str, key, mods)

        copied = json.loads(data_str)
        copied.update(original)
        data[i] = copied

    return data
