import logging
import re

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")

# A mention is any word starting with @ followed by one or more word characters
mention_rx = re.compile(r'@([\w\-]+)')


def find_mentions(inp):
    """Finds any @mentions within the supplied input.

    @mentions are defined as an @ sign, followed by one or more word characters.
    For our purposes, we'll use the \w regex match to signify a word character
    (alphanumeric plus underscores) and also support a hyphen"""

    return mention_rx.findall(inp)
