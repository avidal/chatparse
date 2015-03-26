import json

from .links import find_links
from .mentions import find_mentions
from .emoticons import find_emoticons


def parse(inp, as_json=True):
    """Parses the input text `inp`."""

    rv = dict()
    links = find_links(inp)
    mentions = find_mentions(inp)
    emoticons = find_emoticons(inp)

    # The example cases show that empty results don't show up as keys, which is
    # why we're checking here
    if links:
        rv['links'] = links

    if mentions:
        rv['mentions'] = mentions

    if emoticons:
        rv['emoticons'] = emoticons

    if as_json:
        return json.dumps(rv)
    else:
        return rv
