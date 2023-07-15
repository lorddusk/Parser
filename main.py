import asyncio
import sys
from subprocess import Popen, PIPE, STDOUT

from lib import logger

log = logger.logger

fileList = ['backgrounds', 'bestiary', 'bestiaryFluff', 'classes', 'feats', 'items', 'names', 'races', 'spells', 'psionics',
            'conditionsdiseases', 'deities', 'objects', 'trapshazards', 'cultsboons', 'rewards', 'loot']

fileList = ['bestiary']

async def run():
    open(f'./logs/homebrewTrace.log', 'w').close()
    open(f'./logs/HPFN.log', 'w').close()
    for file in fileList:
        with Popen(f"python ./parser/{file}.py", stdout=PIPE, stderr=STDOUT, bufsize=1, shell=True) as p, \
                open(f'./logs/{file}.log', 'wb') as file:
            for line in p.stdout:  # b'\n'-separated lines
                sys.stdout.buffer.write(line)  # pass bytes as is
                file.write(line)


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
