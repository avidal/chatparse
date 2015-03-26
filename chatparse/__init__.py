import json

from .links import find_links
from .mentions import find_mentions
from .emoticons import find_emoticons


def parse(inp, as_json=True):
    """Parses the input text `inp`."""

    rv = dict()
    rv['links'] = find_links(inp)
    rv['mentions'] = find_mentions(inp)
    rv['emoticons'] = find_emoticons(inp)

    if as_json:
        return json.dumps(rv)
    else:
        return rv
