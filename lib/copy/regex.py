import re


def return_first_match(text, pattern):
    try:
        result = re.search(pattern, text)
        result = result.group()
    except Exception:
        result = None
    return result