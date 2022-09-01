def spellMarkdown(data, file):
    s = f"#### {data['name']}\n"
    s += f"*{get_level(data['level'])} {get_school(data['school'])}"
    if data.get('ritual', False) is not False:
        s += " (ritual)"
    s += "*\n___\n"
    s += f"- **Casting Time:** {data['casttime']}\n"
    s += f"- **Range:** {data['range']}\n"
    s += f"- **Components:** {data['components']}\n"
    s += f"- **Duration:** {data['duration']}\n"
    s += "___\n"
    description = data['description'].replace("\n", "\n\n")
    s += f"{description}"
    if data.get('higherlevels', None) is not None:
        s += f"\n\n***At Higher Levels.*** {data['higherlevels']}"
    file.write(encoding(s))


def deityMarkdown(data, file):
    if data.get('title', None) is not None:
        s = f"#### {data['name']}, {data['title']}"
    else:
        s = f"#### {data['name']}"
    s += "\n___\n"
    if data.get("category", None) is not None:
        s += f"\n- **Pantheon:** {data['pantheon']} ({data['category']})"
    else:
        s += f"\n- **Pantheon:** {data['pantheon']}"
    s += f"\n- **Alignment:** {', '.join(data['alignment'])}"
    s += f"\n- **Domains:** {', '.join(data['domains'])}"
    if data.get('province', None) is not None:
        s += f"\n- **Province:** {data['province']}"
    if data.get('symbol', '?') != "?":
        s += f"\n- **Symbol:** {data['symbol']}"
    s += "\n___\n"
    if data.get('text', '') != '':
        description = data['text'].replace("\n", "\n\n")
        s += f"\n### Information\n\n{description}"
    file.write(encoding(s))


def encoding(string):
    return string.replace("\u2212", "-")


def get_school(school):
    return {
        "A": "abjuration",
        "V": "evocation",
        "E": "enchantment",
        "I": "illusion",
        "D": "divination",
        "N": "necromancy",
        "T": "transmutation",
        "C": "conjuration"
    }.get(school, school)


def get_level(input):
    if input == 0:
        return "cantrip"
    if input == 1:
        return "1st-level"
    if input == 2:
        return "2nd-level"
    if input == 3:
        return "3rd-level"
    return f"{input}th-level"
