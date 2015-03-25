# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from .. import links


def test_normal_links():

    cases = [
        ("my blog is at https://medium.com/@avidal/",
         ["https://medium.com/@avidal/"]),
        ("twitter.co.uk",
         ["twitter.co.uk"]),
        ("sweet link a-horse.isa.horse/of-course/of-course",
         ["a-horse.isa.horse/of-course/of-course"]),
        ("did you know that .goog is an actual tld?",
         []),
        ("wrapping (in-parens.com)",
         ["in-parens.com"]),
        ("we don't match the trailing-period.goog.",
         ["trailing-period.goog"]),
        ("\nnewlines.com\n",
         ["newlines.com"]),
        ("check out sam jackson: butt.holdings and the sam jackson generator: slipsum.com",
         ["butt.holdings", "slipsum.com"]),
        ("""a big list o links:
            - google.com
            - butt.holdings
            - http://medium.com/@alex/what/
            - 127.0.0.1.xip.io
            - http://127.0.0.1/testing/""",
         ['google.com', 'butt.holdings', 'http://medium.com/@alex/what/',
          '127.0.0.1.xip.io',
          'http://127.0.0.1/testing/']),
        ('-invalid-leader.com', []),
    ]

    for inp, expected in cases:
        actual = links.extract_links(inp)
        assert actual == expected


def test_fallbacks():
    """Asserts that the fallback regular expression will match a wide range of
    links, even if they don't have a valid tld. Most of these test cases were
    taken directly from the HipChat OSX client."""

    cases = (
        ('http://--/', ['http://--/']),
        ('http://chrono.local:8080/', ['http://chrono.local:8080/']),
        ('http://localhost/testing/', ['http://localhost/testing/']),
    )

    for inp, expected in cases:
        actual = links.extract_links(inp)
        assert actual == expected


def test_international_domains():

    # These test cases are taken from the test data provided by
    # publicsuffix.org, hosted here and used as test data by the mozilla network
    # stack:
    # http://mxr.mozilla.org/mozilla-central/source/netwerk/test/unit/data/test_psl.txt?raw=1

    # Note there is some slight doctoring since the test data is about testing
    # public suffixes and so will strip out certain subdomains such as www,
    # which we do not do here.

    cases = (
        (u'食狮.com.cn', [u'食狮.com.cn']),
        (u'食狮.公司.cn', [u'食狮.公司.cn']),
        (u'www.食狮.公司.cn', [u'www.食狮.公司.cn']),
        (u'shishi.公司.cn', [u'shishi.公司.cn']),
        (u'公司.cn', [u'公司.cn']),
        (u'食狮.中国', [u'食狮.中国']),
        (u'www.食狮.中国', [u'www.食狮.中国']),
        (u'shishi.中国', [u'shishi.中国']),
        (u'https://shishi.中国', [u'https://shishi.中国']),
        (u'中国', []),

        # Same as the previous cases, but punycoded this time
        ('xn--85x722f.com.cn', ['xn--85x722f.com.cn']),
        ('xn--85x722f.xn--55qx5d.cn', ['xn--85x722f.xn--55qx5d.cn']),
        ('www.xn--85x722f.xn--55qx5d.cn', ['www.xn--85x722f.xn--55qx5d.cn']),
        ('shishi.xn--55qx5d.cn', ['shishi.xn--55qx5d.cn']),
        ('xn--55qx5d.cn', ['xn--55qx5d.cn']),
        ('xn--85x722f.xn--fiqs8s', ['xn--85x722f.xn--fiqs8s']),
        ('www.xn--85x722f.xn--fiqs8s', ['www.xn--85x722f.xn--fiqs8s']),
        ('shishi.xn--fiqs8s', ['shishi.xn--fiqs8s']),
        ('https://shishi.xn--fiqs8s', ['https://shishi.xn--fiqs8s']),
        ('xn--fiqs8s', []),
    )

    for inp, expected in cases:
        actual = links.extract_links(inp)
        assert actual == expected


def test_schemes():
    """Ensures that each scheme in the valid scheme list is supported against
    a handful of domains."""

    # Each test case will be formatted with a supplied scheme
    base_cases = (
        (u'{0}://google.com', [u'{0}://google.com']),
        (u'{0}://butt.holdings', [u'{0}://butt.holdings']),
        (u'{0}://shishi.中国', [u'{0}://shishi.中国']),
        (u'{0}://shishi.xn--fiqs8s', [u'{0}://shishi.xn--fiqs8s']),
        (u'{0}://localhost/', [u'{0}://localhost/']),
    )

    invalid_schemes = ['alex', 'invalid', 'file', 'telnet', '(gibberish)', '']
    cases = []

    for inp, expected in base_cases:
        for scheme in links.valid_schemes:
            cases.append([inp.format(scheme), [expected[0].format(scheme)]])
        for scheme in invalid_schemes:
            cases.append([inp.format(scheme), []])

    for inp, expected in cases:
        actual = links.extract_links(inp)
        assert actual == expected
