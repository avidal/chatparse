import logging
import re

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")

# An emoticon is 15 or less characters surrounded by parens
emoticon_rx = re.compile(r'\((\w{1,15})\)')


def find_emoticons(inp):

    return emoticon_rx.findall(inp)
