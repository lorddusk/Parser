import logging
import re
import typing
import textwrap
from lib.parse.clazz import *

log = logging.getLogger(__name__)

ABILITY_MAP = {'str': 'Strength', 'dex': 'Dexterity', 'con': 'Constitution',
               'int': 'Intelligence', 'wis': 'Wisdom', 'cha': 'Charisma'}
ATTACK_TYPES = {"M": "Melee", "R": "Ranged", "W": "Weapon", "S": "Spell"}


def render(text, md_breaks=False, join_char='\n', _class=None, subclass=None, options=None, name=""):
    """Parses a list or string from data.
    :returns str - The final text."""
    if isinstance(text, dict):
        text = [text]
    if not isinstance(text, list):
        return parse_data_formatting(str(text))

    out = []
    join_str = f'{join_char}' if not md_breaks else f'  {join_char}'

    for entry in text:
        if not isinstance(entry, dict):
            out.append(str(entry))
        elif isinstance(entry, dict):
            if 'type' not in entry and 'title' in entry:
                out.append(f"**{entry['title']}**: {render(entry['text'], _class=_class, subclass=subclass, options=options)}")

            elif 'type' not in entry and 'istable' in entry:  # only for races
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else ''
                temp += ' - '.join(f"**{parse_data_formatting(cl)}**" for cl in entry['thead']) + '\n'
                for row in entry['tbody']:
                    temp += ' - '.join(f"{parse_data_formatting(col)}" for col in row) + '\n'
                out.append(temp.strip())

            elif 'type' not in entry or entry['type'] in ('entries', 'inset'):
                if 'entry' in entry:
                    out.append(entry['entry'])
                else:
                    out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))  # oh gods here we goooooooo

            elif entry['type'] == 'options':
                classOptions = [e for e in entry['entries'] if isinstance(e, dict)]
                for option in classOptions:
                    # log.info(f"Found option for feature below")
                    out.append(render(option, _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'list':
                out.append('\n'.join(f"- {render(t, _class=_class, subclass=subclass, options=options)}" for t in entry['items']))

            elif entry['type'] == 'table':
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else '\n'
                temp += render_table(entry)
                # temp += ' - '.join(f"**{parse_data_formatting(cl)}**" for cl in entry['colLabels']) if 'colLabels' in entry else '' + '\n'
                # temp += '\n'
                # for row in entry['rows']:
                #     temp += ' - '.join(f"{render(col, _class=_class, subclass=subclass, options=options)}" for col in row) + '\n'
                out.append(temp.strip())

            elif entry['type'] == 'invocation':
                pass  # this is only found in options

            elif entry['type'] == 'abilityAttackMod':
                out.append(f"`{entry['name']} Attack Bonus = "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")

            elif entry['type'] == 'abilityDc':
                out.append(f"`{entry['name']} Save DC = 8 + "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")

            elif entry['type'] == 'bonus':
                out.append("{:+}".format(entry['value']))

            elif entry['type'] == 'dice':
                out.append(f"{entry['number']}d{entry['faces']}")

            elif entry['type'] == 'bonusSpeed':
                out.append(f"{entry['value']} feet")

            elif entry['type'] == 'actions':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'attack':
                out.append(f"{' '.join(ATTACK_TYPES.get(t) for t in entry['attackType'])} Attack: "
                           f"{render(entry['attackEntries'], _class=_class, subclass=subclass, options=options)} Hit: {render(entry['hitEntries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'item':
                try:
                    out.append(f"*{entry['name']}* {render(entry['entry'], _class=_class, subclass=subclass, options=options)}")
                except:
                    try:
                        out.append(f"*{entry['name']}* {render(entry['entries'], _class=_class, subclass=subclass, options=options)}")
                    except:
                        pass

            elif entry['type'] == 'itemSub':
                try:
                    out.append(f"*{entry['name']}* {render(entry['entry'], _class=_class, subclass=subclass, options=options)}")
                except:
                    out.append(f"*{entry['name']}* {render(entry['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'cell':
                if 'entry' in entry:
                    out.append(render(entry['entry'], _class=_class, subclass=subclass, options=options))
                else:
                    if 'exact' in entry['roll']:
                        out.append(str(entry['roll']['exact']))
                    else:
                        out.append(f"{str(entry['roll']['min'])} - {str(entry['roll']['max'])}")

            elif entry['type'] == 'inline':
                if 'entries' in entry:
                    string = render(entry['entries'], _class=_class, subclass=subclass, options=options) + 'indefinite maddness.'
                    out.append(string.replace("\n.", ""))

            elif entry['type'] == 'abilityGeneric':
                out.append(f"`{entry['text']}`")

            elif entry['type'] == 'section':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(entry['entries'], _class=_class, subclass=subclass, options=options))

            elif entry['type'] == 'inlineBlock':
                out.append("At 2nd level, you gain two eldritch invocations of your choice. When you gain certain warlock levels, you gain additional invocations of your choice.")

            elif entry['type'] == 'refClassFeature':
                classfeat = entry['classFeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['classFeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getClassFeature(CreateClassSplit(feat), _class)
                out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'refSubclassFeature':
                classfeat = entry['subclassFeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['subclassFeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getSubClassFeature(CreateSubclassSplit(feat), subclass)
                out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            elif entry['type'] == 'refOptionalfeature':
                classfeat = entry['optionalfeature']
                if isinstance(classfeat, dict):
                    feat = classfeat['optionalfeature'].split('|')
                else:
                    feat = classfeat.split('|')
                feature = getOptionalFeature(feat, options)
                if feature is not None:
                    if feature.get('srd', None) is not None:
                        out.append(f"**{feature['name']}**:\n{render(feature['entries'], _class=_class, subclass=subclass, options=options)}")

            else:
                log.warning(f"Missing data entry type parse: {entry}")

        else:
            log.warning(f"Unknown data entry: {entry}")

    return parse_data_formatting(join_str.join(out))


def SRC_FORMAT(e):
    if e is not None:
        return e.split('|')[0] if len(e.split('|')) < 3 else e.split('|')[2]
    else:
        return None


ATK_TYPES = {'mw': "Melee Weapon", 'rw': "Ranged Weapon", 'mw,rw': "Melee or Ranged Weapon",
             'ms': "Melee Spell", 'rs': "Ranged Spell", 'ms,rs': "Melee or Ranged Spell"}
FORMATTING = {'bold': '**', 'italic': '*', 'b': '**', 'i': '*'}
PARSING = {'hit': lambda e: f"+{e}",
           'filter': lambda e: e.split('|')[0],
           'link': lambda e: f"[{e.split('|')[0]}]({e.split('|')[1]})",
           'adventure': lambda e: e.split('|')[0],
           'recharge': lambda e: f"(Recharge {e}-6)" if e else "(Recharge 6)",
           'chance': lambda e: e.split('|')[1] if len(e.split('|')) > 1 else f"{e.split('|')[0]}%",
           'atk': lambda e: f"{ATK_TYPES.get(e, 'Unknown')} Attack:",
           'scaledice': lambda e: e.split('|')[-1],
           'book': lambda e: e.split('|')[0],
           'h': lambda e: "Hit: ",
           'dice': lambda e: e.split('|')[-1]}
DEFAULT = ['condition', 'skill', 'action', 'creature', 'item', 'spell', 'damage', 'race', 'background',
           'class', 'table', 'sense', 'dc']
IGNORE = ['note', '5etools']


def parse_data_formatting(text):
    """Parses a {@format } string."""
    exp = re.compile(r'{@(\w+)(?: ([^{}]+?))?}')

    def sub(match):
        log.debug(f"Rendering {match.group(0)}...")
        if match.group(1) in FORMATTING:
            f = FORMATTING.get(match.group(1), '')
            out = f"{f}{match.group(2)}{f}"
        elif match.group(1) in PARSING:
            f = PARSING.get(match.group(1), lambda e: e)
            if f(match.group(2)) == "Starting Gold":
                out = f"{match.group(0).split('|')[1]}"
            else:
                out = f(match.group(2))
        else:
            out = SRC_FORMAT(match.group(2))
            if not match.group(1) in DEFAULT and not match.group(1) in IGNORE:
                log.warning(f"Possible unknown tag: {match.group(0)}")
        log.debug(f"Replaced with {out}")
        return out

    while exp.search(text):
        text = exp.sub(sub, text)
    return text


def recursive_tag(value):
    """
    Recursively renders all tags.
    :param value: The object to render tags from.
    :return: The object, with all tags rendered.
    """
    if isinstance(value, str):
        return render(value)
    if isinstance(value, list):
        return [recursive_tag(i) for i in value]
    if isinstance(value, dict):
        for k, v in value.items():
            value[k] = recursive_tag(v)
    return value


# When in fullscreen on a 1080p screen at default appearance settings,
#  code blocks inside a Discord embed have a maximum width of 61 characters.
# Formatting based on this means it doesn't look good on mobile devices,
#  but to be fair not much does.
TABLE_MAX_WIDTH = 61

# Tables will be formatted with spaces in between columns when possible.
# This determines the maximum number of spaces that will be placed between
#  columns.
# NOTE: This number INCLUDES the divider bar, which is why all of the options
#  are odd.
TABLE_VALID_COL_SPACINGS = (1, 3)

# By default, columns are left-aligned.
DEFAULT_COL_ALIGN = '<'


def render_table(entry: dict) -> typing.Optional[str]:
    if 'colLabels' in entry:
        # If the table has column labels, insert them as the first row
        table = [entry['colLabels'], *entry['rows']]
    else:
        table = entry['rows']

    # Return `None` if the table is empty
    if not table:
        return None

    table = [render_table_row(row) for row in table]

    # `colStyles` is optional. If it is not given, we default to left-align,
    #   and we determine how much space a column should get based on its
    #   contents.
    col_styles = entry.get('colStyles')
    if col_styles is not None:
        col_styles = parse_col_styles(entry['colStyles'])

    col_widths = calculate_col_widths_before_split(table, col_styles)

    table = split_rows(table, col_widths)

    ret = _render_table(table, col_styles)

    # Wrap the table in a code block
    return f"```{ret}\n```"


def render_table_row(row) -> list[str]:
    if isinstance(row, dict):
        # The row follows the schema given\
        # [here](https://github.com/TheGiddyLimit/TheGiddyLimit.github.io/blob/master/test/schema/entry.json#L388).
        assert row['type'] == 'row'
        return render_table_row(row['row'])
    elif isinstance(row, list):
        # The row is a list of cells. Each one is either a string
        #  or an entry. We let the renderer determine this and format
        #  it as a string
        return [render(cell) for cell in row]
    else:
        raise TypeError(f'Unhandled table row type: `{type(row).__name__}`')


def parse_col_styles(col_styles: list[str]) -> list[tuple[int, str]]:
    """Style widths in the JSON are formatted as
        col-<`width`>[ `align`]
    `width` is a number between 0 and 12. Combined, the values of `width` sum to 12.
    The valid alignment options are `text-left`, `text-center`, and `text-right`.
    If the alignment is not specified, it defaults to `text-left`.

    :return a list of pairs in the form (`width`, `align`)
    """
    ret = []

    for style in col_styles:
        if ' ' in style:
            width, align, *_ = style.split(' ')
            if 'col' not in width:
                dummy = align
                align = width
                width = dummy
        else:
            width, align = style, None

        # Since the values of `width` sum to 12, we use it to approximate how
        #  much space each column should be given. Sometimes these widths are
        #  WAY too high, so we don't naively use it alone.
        width = width.split('-')[1]
        width = int(float(width) * TABLE_MAX_WIDTH / 12)

        # We will use this alignment in `str.format`
        align = {
            'text-left': '<',
            'text-center': '^',
            'text-right': '>',
        }.get(align, DEFAULT_COL_ALIGN)

        ret.append((width, align))
    return ret


def calculate_col_widths_before_split(table: list[list[str]], col_styles: list[tuple[int, str]]) -> list[int]:
    if col_styles is None:
        # If `colStyles` was not given, we use the default alignment
        #  and start out with the available space distributed evenly
        #  among the columns.
        num_cols = len(table[0])
        width, align = TABLE_MAX_WIDTH // num_cols, DEFAULT_COL_ALIGN
        col_styles = [(width, align) for _ in range(num_cols)]
    else:
        num_cols = len(col_styles)

    # The length of the longest entry in each column. This is how much space we would
    #  ideally allocate to each column i.e. without wrapping.
    ideal_widths = [max(len(row[col]) for row in table) for col in range(num_cols)]

    # Since the sum of the `width` values is <= `TABLE_MAX_WIDTH`, the sum of
    #  these values is <= `TABLE_MAX_WIDTH`.
    # If the ideal width is less than the width we allocated the column originally,
    #  we use the ideal width instead, so that we can use the extra space for
    #  other columns.
    actual_widths = [min(style[0], ideal_width) for style, ideal_width in zip(col_styles, ideal_widths)]

    # The difference between the allocated width and the ideal width, scaled to the
    #  ideal width. We use this to determine which column we should allocate extra
    #  space to.
    dist_key = lambda idx: actual_widths[idx] / ideal_widths[idx] - 1

    # While there is still space to allocate AND not all columns have been given their ideal widths,
    #  we allocate a single character of space to the column that needs it the most.
    # TODO: Pretty sure this is equivalent to a voting theory problem, maybe check that out?
    while sum(actual_widths) + num_cols - 1 < TABLE_MAX_WIDTH and\
            any(ideal > actual for ideal, actual in zip(ideal_widths, actual_widths)):
        # Find the column that needs extra space the most
        min_width_idx = min(range(num_cols), key=dist_key)
        # Allocate one character of space to it
        actual_widths[min_width_idx] += 1

    return actual_widths


def split_rows(table: list[list[str]], col_widths: list[int]) -> list[list[list[str]]]:
    """Given the table and the width that each column has been allocated,
    splits the rows into lines so that cells wrap to the next line instead of
    overfilling the embed.
    """
    return [split_row(row, col_widths) for row in table]


def split_row(row: list[str], col_widths: list[int]) -> list[list[str]]:
    """Split a table row into lines, i.e. wrap columns based on the widths
    they have been allocated.
    """
    cells_widths = list(zip(row, col_widths))

    # If all the cells fit on a single line without wrapping, we're done.
    if all(len(cell) <= width for cell, width in cells_widths):
        return [row]

    # Otherwise, we use the `textwrap` library to split each cell into lines.
    row_split = [textwrap.wrap(cell, width=width) for cell, width in cells_widths]

    # The number of lines the row takes up now that it has been split.
    num_lines = max(len(cell) for cell in row_split)

    # At this point, the row is laid out as
    # [
    #   [ r1c1, r2c1, .. ],
    #   [ r1c2, r2c2, .. ],
    #   ..,
    # ]
    # but we want it to be laid out as
    # [
    #   [ r1c1, r1c2, .. ],
    #   [ r2c1, r2c2, .. ],
    #   ..,
    # ]
    # because that's how it will actually be displayed.
    ret = []
    for i in range(num_lines):
        # Append the ith part of the cell to the line if it exists
        ret.append([cell[i] if len(cell) > i else "" for cell in row_split])
    return ret


def calculate_col_widths_after_split(table: list[list[list[str]]]) -> list[int]:
    num_cols = len(table[0][0])
    return [max(len(line[col]) for row in table for line in row) for col in range(num_cols)]


def calculate_col_spacing(col_widths: list[int]) -> int:
    """Calculate the maximum spacing available between columns.
    """
    num_cols = len(col_widths)
    max_available_spacing = (TABLE_MAX_WIDTH - sum(col_widths)) // (num_cols - 1)
    try:
        value = max(x for x in TABLE_VALID_COL_SPACINGS if x <= max_available_spacing)
    except ValueError:
        value = 1
    return value


def get_separators(col_widths: list[int]) -> tuple[str, str]:
    """Returns a tuple (row_sep, col_sep),
    where row_sep is the line separator between rows of the table,
    and col_sep is the string that separates columns in the same row.
    """

    num_cols = len(col_widths)
    col_spacing = calculate_col_spacing(col_widths)

    row_sep = "\n" + "-" * (sum(col_widths) + col_spacing * (num_cols - 1))

    half_spacing = col_spacing // 2
    current_idx = 0
    for width in col_widths[:-1]:
        current_idx += width + half_spacing + 1
        row_sep = row_sep[:current_idx] + "+" + row_sep[current_idx + 1:]
        current_idx += half_spacing

    col_sep = " " * half_spacing
    col_sep = f"{col_sep}|{col_sep}"

    return row_sep, col_sep


def get_col_style_format_strings(col_styles: list[tuple[int, str]], col_widths: list[int]) -> list[str]:
    """Build the `str.format` fields based on `colStyles`.
    """
    return ["{:%s%s}" % (align, width) for (_, align), width in zip(col_styles, col_widths)]


def _render_table(table: list[list[list[str]]], col_styles: list[tuple[int, str]]) -> str:
    num_rows = len(table)

    col_widths = calculate_col_widths_after_split(table)
    row_separator, col_separator = get_separators(col_widths)

    styles = get_col_style_format_strings(col_styles, col_widths)

    buf = ""
    for i, row in enumerate(table):
        for line in row:
            styled_cells = (style.format(cell.lstrip()) for style, cell in zip(styles, line))
            buf += "\n" + col_separator.join(styled_cells)
        if i != num_rows - 1:
            buf += row_separator
    return buf.rstrip()
