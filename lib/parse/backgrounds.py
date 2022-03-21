import logging

from lib.parsing import render

log = logging.getLogger("backgrounds")

SRD = ['Acolyte']
PROF_KEYS = ("skillProficiencies", "languageProficiencies", "toolProficiencies")

def srdfilter(data):
    for background in data:
        if background['name'] in SRD:
            background['srd'] = True
        else:
            background['srd'] = False
    return data

def parseBackgrounds(data):
    out = []
    for raw in data:
        log.info(f"Parsing {raw['name']}...")
        profs = parse_profs(raw)
        traits, fluff = parse_traits(raw)

        if fluff is not None:
            background = {
                "name": raw['name'],
                "info": fluff.get('fluff'),
                "proficiencies": profs,
                "traits": traits,
                "source": raw['source'],
                "page": raw.get('page', '?')
            }
        else:
            background = {
                "name": raw['name'],
                "info": '',
                "proficiencies": profs,
                "traits": traits,
                "source": raw['source'],
                "page": raw.get('page', '?')
            }
        out.append(background)
    return out


def parse_profs(raw):
    profs = {}
    for proftype in PROF_KEYS:
        profname = proftype[:-13]
        if proftype in raw:
            profs[profname] = []
            for prof in raw[proftype]:
                if 'choose' in prof:
                    profs[profname].append(' or '.join(p for p in prof['choose']['from']))
                elif 'any' in prof:
                    profs[profname].append(f"any {prof['any']} {profname}{'s' if prof['any'] > 1 else ''}")
                else:
                    profs[profname].extend(k for k in prof.keys())
    return profs


def parse_traits(raw):
    traits = []
    fluff = {}
    for entry in raw['entries']:
        if isinstance(entry, list):
            entry = entry[0]
        if not isinstance(entry, str):
            try:
                if entry['type'] == 'list':
                    for item in entry['items']:
                        trait = {
                            'name': item['name'],
                            'text': render(item.get('entry') or item.get('entries'))
                        }
                        traits.append(trait)
                elif entry['type'] in ('entries', 'section'):
                    trait = {
                        'name': entry.get('name', ''),
                        'text': render(entry['entries'])
                    }
                    traits.append(trait)
                elif entry['type'] == 'table':
                    trait = {
                        'name': entry.get('caption', ''),
                        'text': render(entry['rows'])
                    }
                    traits.append(trait)
                else:
                    log.warning(f"Unknown entry: {entry}")
                    continue
            except KeyError:
                try:
                    trait = {
                        'name': entry.get('name', ''),
                        'text': render(entry['entries'])
                    }
                    traits.append(trait)
                except:
                    log.warning(f"Unknown entry: {entry}")
                    continue
        else:
            fluff = {
                'fluff': entry
            }
    return traits, fluff
