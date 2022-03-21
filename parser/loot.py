import asyncio
import logging

from lib.utils import get_data, dump

log = logging.getLogger("loot")


def get_items():
    return get_data("loot.json")['magicItems']


def clean_tables(tables):
    out = []
    for t in tables:
        log.info(f"Parsing items for {t['name']}")
        entries = []
        currentIndex = 1
        for entry in t['table']:
            min = entry['min']
            max = entry['max']
            if entry.get('item') is not None:
                item = entry['item'].replace("{@item ","").replace("}","")
            if entry.get('choose') is not None:
                if entry.get('choose').get('fromGroup') is not None:
                    item = entry.get('choose').get('fromGroup')[0]
                if entry.get('choose').get('fromGeneric') is not None:
                    item = entry.get('choose').get('fromGeneric')[0]
            amount = (max-min)+1
            for i in range(amount):
                entry = {
                    "index": currentIndex,
                    "item": item
                }
                currentIndex += 1
                entries.append(entry)
        table = {
            "name" : t['name'],
            "items": entries
        }
        out.append(table)
    return out


async def run():
    data = get_items()
    data = clean_tables(data)
    await dump(data, 'loot.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")