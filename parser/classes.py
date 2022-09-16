from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import asyncio
import logging

from lib.parse.clazz import *
from lib.parsing import recursive_tag, render
from lib.utils import dump, dump_classfeats, fix_dupes, get_data, get_indexed_datas, remove_ignored, srdonly, \
    camel_to_title

SRD = ('Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Warlock',
       'Wizard')
SRD_SUBCLASSES = (
    'Path of the Berserker', 'College of Lore', 'Life Domain', 'Circle of the Land', 'Champion', 'Way of the Open Hand',
    'Oath of Devotion', 'Hunter', 'Thief', 'Draconic Bloodline', 'The Fiend', 'School of Evocation'
)
IGNORED_SOURCES = ('Stream', 'UASidekicks', 'UAPrestigeClassesRunMagic', 'UA2021MagesOfStrixhaven', 'UAArtificer', 'UAArtificerRevisited', 'UAModifyingClasses', 'UARanger', 'UATheRangerRevised')
SOURCE_HIERARCHY = ('FTD', 'TCE', 'ERLW', 'MTF', 'VGM', 'XGE', 'PHB', 'DMG', 'GGR', 'SCAG', 'UAWGE', 'UA', 'UA2020PsionicOptionsRevisited', 'nil')

log = logging.getLogger("libs")


def get_class_from_web():
    return get_indexed_datas('class/', ['class', 'subclass', 'classFeature', 'subclassFeature'])


def filter_ignored(data):
    data = remove_ignored(data, IGNORED_SOURCES)
    for _class in data:
        if _class.get('subclasses') is not None:
            _class['subclasses'] = remove_ignored(_class['subclasses'], IGNORED_SOURCES, True)

    return data


def srdfilter(data):
    for _class in data:
        if _class['name'] in SRD:
            _class['srd'] = True
        else:
            _class['srd'] = False

        if _class.get('subclasses') is not None:
            for subclass in _class['subclasses']:
                if subclass['name'] in SRD_SUBCLASSES:
                    subclass['srd'] = True
                elif "(UA)" in subclass['name']:
                    subclass['srd'] = False
                else:
                    subclass['srd'] = False
    return data


def parse_subclass_feats(subfeatdata, optfeats, featdata, out):
    for feat in subfeatdata:
        if feat.get("classSource", None) not in IGNORED_SOURCES and feat.get("source", None) not in IGNORED_SOURCES:
            if feat.get("srd", None) is None:
                srd = False
            else:
                srd = feat.get("srd")
            feat = CreateSubclassFeature(feat['className'],
                                         feat['subclassShortName'],
                                         feat['name'],
                                         render(feat['entries'], _class=featdata, subclass=subfeatdata, options=optfeats),
                                         feat['level'],
                                         feat['subclassSource'],
                                         srd)
            out.append(feat)
    return out


def parse_class_feats(featdata, optfeats, out):
    for feature in featdata:
        if feature.get("source", None) not in IGNORED_SOURCES:
            if feature.get("srd", None) is None:
                srd = False
            else:
                srd = feature.get("srd")
            feat = CreateClassFeature(feature['className'], feature['name'],
                                      render(feature['entries'], _class=featdata, options=optfeats), feature['level'],
                                      feature['classSource'], srd)
            out.append(feat)
    return out


def _resolve_name(entry):
    """Resolves the next name of a data entry.
    :param entry (dict) - the entry.
    :returns str - The next found name, or None."""
    if 'entries' in entry and 'name' in entry['entries'][0] and isinstance(entry['entries'][0], dict):
        return _resolve_name(entry['entries'][0])
    elif 'name' in entry:
        return entry['name']
    else:
        log.warning(f"No name found for {entry}")


def parse_invocations():
    out = []
    optfeats = get_data('optionalfeatures.json')['optionalfeature']
    invocs = [i for i in optfeats if i['featureType'] == 'EI']

    for invoc in invocs:
        log.info(f"Parsing invocation {invoc['name']}")
        text = render(invoc['entries'])
        if 'prerequisite' in invoc:
            prereqs = []
            for prereq in invoc['prerequisite']:
                for key in prereq.keys():
                    if key == 'pact':
                        prereqs.append(f"Pact of the {prereq[key]}")
                    elif key == 'patron':
                        prereqs.append(f"Patron: {prereq[key]}")
                    elif key == 'level':
                        prereqs.append(f"Level {prereq[key]['level']}")
                    elif key == 'spell':
                        spell = camel_to_title(prereq[key][0])
                        if '#C' in spell:
                            prereqs.append(f"*{spell.replace('#C', '')}* cantrip")
                        elif '/Curse#X' in spell:
                            prereqs.append(f"*{spell.replace('/Curse#X', '')}* spell or a warlock feature that curses")
                        else:
                            prereqs.append(f"*{spell}* spell")

                    else:
                        log.warning(f"Unknown prereq type: {key}")
            text = f"*Prerequisite: {', '.join(prereqs)}*\n{text}"
        if invoc['source'] != "PHB" and invoc['source'] != "XGE":
            inv = {
                'name': f"Warlock: Eldritch Invocation: {invoc['name']} ({invoc['source']})",
                'text': text,
                'srd': invoc['source'] == 'PHB'
            }
        else:
            inv = {
                'name': f"Warlock: Eldritch Invocation: {invoc['name']}",
                'text': text,
                'srd': invoc['source'] == 'PHB'
            }
        out.append(inv)
    return out


def parse_maneuvers():
    out = []
    optfeats = get_data('optionalfeatures.json')['optionalfeature']
    maneuvers = [i for i in optfeats if 'MV' in i['featureType']]

    for maneuver in maneuvers:
        log.info(f"Parsing maneuver {maneuver['name']}")
        text = render(maneuver['entries'])
        if maneuver['source'] != "PHB":
            man = {
                'name': f"Battle Master: Maneuver: {maneuver['name']} ({maneuver['source']})",
                'text': text,
                'srd': maneuver['source'] == 'PHB'
            }
        else:
            man = {
                'name': f"Battle Master: Maneuver: {maneuver['name']}",
                'text': text,
                'srd': maneuver['source'] == 'PHB'
            }
        out.append(man)
    return out


def fix_subclass_dupes(data):
    for _class in data:
        if 'subclasses' in _class:
            _class['subclasses'] = fix_dupes(_class['subclasses'], SOURCE_HIERARCHY)
    return data


def class_srdonly(data):
    for klass in data:
        if 'subclasses' not in klass:
            continue
        klass['subclasses'] = srdonly(klass['subclasses'])
    return srdonly(data)


def class_classfeats(data):
    for _class in data:
        if 'classFeatures' in _class:
            i = 0
            for classfeat in _class['classFeatures']:
                if isinstance(classfeat, dict):
                    feat = classfeat['classFeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = CreateClassSplit(feat)
                _class['classFeatures'][i] = feature
                i += 1
    return data


def subclass_classfeats(data):
    for _class in data:
        if 'subclasses' in _class:
            for subclass in _class['subclasses']:
                i = 0
                if 'subclassFeatures' in subclass:
                    for classfeat in subclass['subclassFeatures']:
                        if isinstance(classfeat, dict):
                            feat = subclass['subclassFeatures'].split('|')
                        else:
                            feat = classfeat.split('|')
                        feature = CreateSubclassSplit(feat)
                        subclass['subclassFeatures'][i] = feature
                        i += 1
        else:
            print("NO SUBCLASSES DETECTED", _class['name'])
    return data


async def run():
    data, classfeatsdata, subclassfeatsdata = get_class_from_web()
    data = filter_ignored(data)
    data = srdfilter(data)
    data = recursive_tag(data)
    data = fix_dupes(data, SOURCE_HIERARCHY)
    data = fix_subclass_dupes(data)
    data = class_classfeats(data)
    data = subclass_classfeats(data)
    await dump(data, 'classes.json')

    optfeats = get_data('optionalfeatures.json')['optionalfeature']
    classfeats = []
    classfeats = parse_class_feats(classfeatsdata, optfeats, classfeats)
    classfeats = parse_subclass_feats(subclassfeatsdata, classfeatsdata, optfeats, classfeats)

    classfeats.extend(parse_invocations())
    classfeats.extend(parse_maneuvers())
    await dump_classfeats(classfeats, 'classfeats.json')


if __name__ == '__main__':
    import time

    s = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.2f} seconds.")
