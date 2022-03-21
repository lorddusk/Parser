import asyncio
import logging

from lib.utils import dump, get_data
import lib.parsingmethods as pm

log = logging.getLogger("conditionsdiseases")


def get_latest_conditions():
    return get_data("conditionsdiseases.json")['condition']

def get_latest_diseases():
    return get_data("conditionsdiseases.json")['disease']


async def run():
    data = get_latest_conditions()
    data = pm.parse_condition(data)
    await dump(data, 'conditions.json')
    data = get_latest_diseases()
    data = pm.parse_disease(data)
    await dump(data, 'diseases.json')

if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")