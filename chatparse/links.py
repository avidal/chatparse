import logging
import os
import re

import lxml.html
import requests

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel("DEBUG")


# A frozen-set of TLDs, prepared using tldextract module
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'tlds.pkl')) as f:
    tlds = pickle.load(f)

# Turn the set of tlds into a regular expression; kind of a heavy regex but it's
# the simplest thing that will work.
# For each tld, we want to prefix it with a dot (since it's not like that in the
# set), and encode it with idna (see RFC 3490)
tlds = [re.escape(u'.' + tld.encode('idna')) for tld in tlds]

# In order for a domain in the input text to match, the tld must appear in one
# of the following forms:
#  - example.com/
#  - example.com:\d+/? (colon plus port with an optional slash)
#  - example.com\W (a non-word character)
#  - example.com\s (any space character)
# In addition, any one of the above examples may end with a newline
tld_rx = re.compile(u'({0})(?:\W|\s|/|\:[\d]+)?\$?'.format(u'|'.join(tlds)), re.UNICODE)

# Ordinals of chars that are valid in hostnames
# 97-122 covers a-z, 45-59 covers 0-9, hyphen, period, slash, and colon
# while colon and slash aren't actually valid in hostnames, it works in the
# general case to allow us to walk left from a tld to find the beginning of the
# url
valid_hostname_chars = set(map(chr, (range(97, 123) + range(45, 59))))

# A set of valid schemes that we support. Note, this was taken from doing some
# basic tests against the existing hipchat client.
valid_schemes = set(['http', 'https', 'ftp', 'ssh', 'mailto', 'git', 'svn', 'hg'])

# An inexhaustive list of characters invalid in the path portion of a url. This
# is used to scan forward in an input after matching a tld so we can find the
# end of the link.
invalid_path_chars = set([')', ' ', "\t", "\r", "\n"])

# A fallback regular expression that attempts to match things that look like
# urls. This should only need to be used in cases where we are resolving things
# like http://localhost/ or http://chrono.local/
# Note that this is intentionally open to invalid hostnames in an attempt to
# minimize false negatives
fallback_url_rx = re.compile(u'((?:{0})://[a-z0-9\.\-]+)'.format(u'|'.join(valid_schemes)), re.UNICODE)


def fetch_title(url):
    """Uses requests to get the url, then lxml to find the text in the <title>
    tag."""

    # Very naive cache. In a real environment I'd use whatever cache
    # infrastructure I had available, perhaps redis or memcached.
    if not hasattr(fetch_title, "_cache"):
        fetch_title._cache = dict()

    # First, we normalize the url, returning None if there's a scheme and it's
    # not http or https

    # Strip off any leading : or slashes
    # (avoids things like ://example.com which we can actually resolve to http
    # in some cases)
    url = url.lstrip(u':/')

    parsed = urlparse.urlparse(url)
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return None

    if not parsed.scheme:
        url = u'http://{0}'.format(url)
    else:
        url = parsed.geturl()

    if url in fetch_title._cache:
        return fetch_title._cache[url]

    try:
        # Only wait for half a second to get a response
        resp = requests.get(url, timeout=0.5)
    except requests.RequestException:
        logger.exception(u"Caught exception fetching title for %s", url)
        return None

    # If the response has a not-ok status code, return None
    if not resp.ok:
        return None

    # If there's no body text, return None
    if len(resp.text) == 0:
        return None

    tree = lxml.html.fromstring(resp.text)
    title = tree.xpath('//html/head/title/text()')

    # xpath will give back a tuple, we only care about the first item
    if not title or not len(title):
        title = None
    else:
        title = title[0]

    fetch_title._cache[url] = title
    return title


def extract_links(inp, links=None):
    """Scan over the input, looking for links.

    Links are detected by first looking for a matching tld and then searching
    around the matching tld. If a tld is not located, we fall back to
    a simplistic url matching regular expression.

    Returns a list of detected links in the input text.
    """
    if not links:
        links = []

    if not inp:
        # Once we run out of input, just return the links
        logger.debug("No input. Returning accumulated links %r", links)
        return links

    # Make sure the input is idna encoded to support internationalized domain
    # names. idna encoding will fail on invalid input and in those cases we'll
    # just continue on with the unicode
    logger.debug("Attempting to encode input %r", inp)
    must_decode_idna = False
    try:
        encoded = inp.encode("idna")

        # If the encoded version and the input version are identical, then
        # prefer the input version. This allows us to deal with situations where
        # the input is *already* idna encoded.
        if encoded != inp:
            inp = encoded
            must_decode_idna = True

    except UnicodeError:
        logger.debug("Failed to encode to idna.")
        pass

    logger.debug("Searching for links on input %r", inp)
    match = tld_rx.search(inp)
    if not match:
        logger.debug("  No tld found. Checking fallback urls.")

        # If we can't find a tld, then we can try for a simple regular
        # expression to match common cases such as http://localhost/ or
        # http://macbook-pro.local Basically, catch anything that matches
        # scheme://hostname/
        match = fallback_url_rx.search(inp)
        if not match:
            logger.debug("  No url found. Returning accumulated links %r.", links)
            return links

    matched = match.group(1)
    logger.debug("  Found match %s", matched)

    # Start and end are the offsets where the regular expression was matched
    start, end = match.span(1)
    head, tail = inp[:start], inp[end:]
    logger.debug("  Scanning head %r", head)
    logger.debug("  and tail %r", tail)

    # prefix and suffix are used to accumulate the bytes from the head and tail
    # that are part of the url
    prefix, suffix = "", ""

    # Now, we can search from the head backwards until we find a character
    # that's invalid in a hostname, which would be anything other than a-z, 0-9,
    # and a hyphen
    for ch in head[::-1]:
        ch = ch.lower()

        if ch not in valid_hostname_chars:
            break

        prefix += ch

    # Same goes for the path component. Since we don't require the input to be
    # urlencoded, we can end up with almost anything in here; so we scan forward
    # to the first space or paren.
    for ch in tail:
        ch = ch.lower()
        if ch in invalid_path_chars:
            logger.debug("    invalid")
            break

        suffix += ch

        # Move the tail forward one char after consuming it for the suffix
        tail = tail[1:]

    # Reverse the prefix, since we scanned backwards
    prefix = prefix[::-1]

    # If the suffix has a trailing period, remove it and push it back onto the
    # tail
    if suffix.endswith("."):
        suffix = suffix[:-1]
        tail += "."

    link = u"{}{}{}".format(prefix, matched, suffix)

    # Perform a few sanity checks against the link before considering it golden.
    # These are chars that are valid in the scheme://hostname scan, but aren't
    # valid as a starting character
    if link[0] in ('.', '/', '\\', ':', '-'):
        logger.debug("  Invalid prefix %r", link[0])
        return extract_links(tail, links)

    # Attempt to decode the link back from idna if it was encoded in the first
    # place
    if must_decode_idna:
        link = link.decode("idna")

    # Final santiy check, ensure the link parses via urlparse and validate the
    # scheme. Note that the default scheme is http
    parsed = urlparse.urlparse(link, scheme='http')

    if parsed.scheme not in valid_schemes:
        return extract_links(tail, links)

    links.append(link)

    # And recurse, looking for links in the remaining input
    return extract_links(tail, links)


def find_links(inp):
    """Extracts links from the provided input, returns a list of dictionaries of
    the form:
    {
        "title": "<page title>",
        "url": "<url found>"
    }
    """

    rv = []
    links = set(extract_links(inp))

    # For each url, fetch the page title
    for link in links:
        title = fetch_title(link)
        rv.append(dict(url=link, title=title))

    return rv
