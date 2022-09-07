import asyncio
import copy
import fnmatch
import json
import logging
import re

from lib.copy import checkCopyMeta
from lib.parsing import recursive_tag, render
from lib.utils import diff, dump, get_data, srdonly, fix_dupes
import lib.parsingmethods as pm


log = logging.getLogger("items")

ITEM_TYPES = {"G": "Adventuring Gear", "SCF": "Spellcasting Focus", "AT": "Artisan Tool", "T": "Tool",
              "GS": "Gaming Set", "INS": "Instrument", "A": "Ammunition", "M": "Melee Weapon", "R": "Ranged Weapon",
              "LA": "Light Armor", "MA": "Medium Armor", "HA": "Heavy Armor", "S": "Shield", "W": "Wondrous Item",
              "P": "Potion", "ST": "Staff", "RD": "Rod", "RG": "Ring", "WD": "Wand", "SC": "Scroll", "EXP": "Explosive",
              "GUN": "Firearm", "SIMW": "Simple Weapon", "MARW": "Martial Weapon", "$": "Valuable Object",
              'TAH': "Tack and Harness", 'TG': "Trade Goods", 'MNT': "Mount", 'VEH': "Vehicle", 'SHP': "Ship",
              'GV': "Generic Variant", 'AF': "Futuristic", 'siege weapon': "Siege Weapon", 'generic': "Generic"}

DMGTYPES = {"B": "bludgeoning", "P": "piercing", "S": "slashing", "N": "necrotic", "R": "radiant"}

SIZES = {"T": "Tiny", "S": "Small", "M": "Medium", "L": "Large", "H": "Huge", "G": "Gargantuan"}

PROPS = {"A": "ammunition", "LD": "loading", "L": "light", "F": "finesse", "T": "thrown", "H": "heavy", "R": "reach",
         "2H": "two-handed", "V": "versatile", "S": "special", "RLD": "reload", "BF": "burst fire", "CREW": "Crew",
         "PASS": "Passengers", "CARGO": "Cargo", "DMGT": "Damage Threshold", "SHPREP": "Ship Repairs"}

SOURCE_HIERARCHY = ('TCE', 'MTF', 'VGM', 'PHB', 'DMG', 'GGR', 'MOT', 'VRGR', 'UA', 'nil')


def get_latest_items():
    return get_data("items.json")['item'] + get_data("magicvariants.json")['magicvariant'] + get_data("items-base.json")['baseitem']


def srdfilter(data):
    transforms = {}
    patterns = []
    with open('./srd/srd-items.txt') as f:
        for srditem in f.read().split('\n'):
            if ':' in srditem:
                old, new = srditem.split(':')
                transforms[old.lower().strip()] = new.lower().strip()
            elif '*' in srditem:
                patterns.append(srditem.lower().strip())
            else:
                transforms[srditem.lower().strip()] = srditem.lower().strip()
    found = set()

    for item in data:
        is_srd = False
        item_name = item['name'].lower()
        if item.get('source') not in ('PHB', 'DMG', None):
            is_srd = False
        elif item.get('source') == 'PHB' and not item.get('wondrous'):
            is_srd = True
            found.add(item_name)
        else:
            if item_name in transforms:
                if transforms[item_name] == item_name:
                    is_srd = True
                    found.add(item_name)
                else:
                    new_item = copy.deepcopy(item)
                    new_item['name'] = transforms[item_name].title()
                    transforms[transforms[item_name]] = transforms[item_name]  # make sure we grab it
                    data.append(new_item)

            for pattern in patterns:
                if fnmatch.fnmatch(item_name, pattern):
                    log.info(f"{item_name} matches {pattern}")
                    is_srd = True
                    found.add(item_name)
        item['srd'] = is_srd

    not_found = [s for s in transforms if s not in found]
    log.warning(f"These SRD items were not found: {', '.join(not_found)}")
    return data


def site_render(data):
    out = []
    for item in data:
        if not item['srd']:
            continue

        damage = ''
        extras = ''
        properties = []

        if 'type' in item:
            type_ = ', '.join(
                i for i in ([ITEM_TYPES.get(t, 'n/a') for t in item['type'].split(',')] +
                            ["Wondrous Item" if item.get('wondrous') else ''])
                if i)
            for iType in item['type'].split(','):
                if iType in ('M', 'R', 'GUN'):
                    damage = f"{item.get('dmg1', 'n/a')} {DMGTYPES.get(item.get('dmgType'), 'n/a')}" \
                        if 'dmg1' in item and 'dmgType' in item else ''
                    type_ += f', {item.get("weaponCategory")}'
                if iType == 'S': damage = f"AC +{item.get('ac', 'n/a')}"
                if iType == 'LA': damage = f"AC {item.get('ac', 'n/a')} + DEX"
                if iType == 'MA': damage = f"AC {item.get('ac', 'n/a')} + DEX (Max 2)"
                if iType == 'HA': damage = f"AC {item.get('ac', 'n/a')}"
                if iType == 'SHP':  # ships
                    extras = f"Speed: {item.get('speed')}\nCarrying Capacity: {item.get('carryingcapacity')}\n" \
                        f"Crew {item.get('crew')}, AC {item.get('vehAc')}, HP {item.get('vehHp')}"
                    if 'vehDmgThresh' in item:
                        extras += f", Damage Threshold {item['vehDmgThresh']}"
                if iType == 'siege weapon':
                    extras = f"Size: {SIZES.get(item.get('size'), 'Unknown')}\n" \
                        f"AC {item.get('ac')}, HP {item.get('hp')}\n" \
                        f"Immunities: {item.get('immune')}"
        else:
            type_ = ', '.join(
                i for i in ("Wondrous Item" if item.get('wondrous') else '', item.get('technology')) if i)
        rarity = str(item.get('rarity')).replace('None', '')
        if 'tier' in item:
            if rarity:
                rarity += f', {item["tier"]}'
            else:
                rarity = item['tier']
        type_and_rarity = type_ + (f", {rarity}" if rarity else '')
        value = (item.get('value', 'n/a') + (', ' if 'weight' in item else '')) if 'value' in item else ''
        weight = (item.get('weight', 'n/a') + (' lb.' if item.get('weight') == '1' else ' lbs.')) \
            if 'weight' in item else ''
        weight_and_value = value + weight
        for prop in item.get('property', []):
            if not prop: continue
            a = b = prop
            a = PROPS.get(a, 'n/a')
            if b == 'V': a += " (" + item.get('dmg2', 'n/a') + ")"
            if b in ('T', 'A'): a += " (" + item.get('range', 'n/a') + "ft.)"
            if b == 'RLD': a += " (" + item.get('reload', 'n/a') + " shots)"
            properties.append(a)
        properties = ', '.join(properties)
        damage_and_properties = f"{damage} - {properties}" if properties else damage
        damage_and_properties = (' --- ' + damage_and_properties) if weight_and_value and damage_and_properties else \
            damage_and_properties

        meta = f"*{type_and_rarity}*\n{weight_and_value}{damage_and_properties}\n{extras}"
        text = item['desc']

        out.append({'name': item['name'], 'meta': meta, 'desc': text})
    return out


def parse_copies(data):
    for i, items in enumerate(data):
        if '_copy' not in items:
            continue
        original = items.copy()  # how ironic
        del original['_copy']

        copymeta = items['_copy']
        log.info(f"Copying {copymeta['name']} onto {items['name']}...")
        to_copy = next(m for m in data if m['source'] == copymeta['source'] and m['name'] == copymeta['name'])

        data_str = json.dumps(to_copy)
        if copymeta.get('_mod', None) is not None:
            for key, mods in copymeta.get('_mod', []).items():
                data_str = checkCopyMeta(data_str, key, mods)

        copied = json.loads(data_str)
        copied.update(original)
        data[i] = copied
    return data


async def run():
    data = get_latest_items()
    data = parse_copies(data)
    data = pm.moneyfilter(data)
    data = pm.variant_inheritance(data)
    data = srdfilter(data)
    data = pm.prerender(data)
    data = fix_dupes(data, SOURCE_HIERARCHY, True)
    # sitedata = site_render(data)
    await dump(data, 'items.json')
    # dump(sitedata, 'template-items.json')
    # await dump(srdonly(data), 'srd-items.json')
    # diff('srd/srd-items.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
