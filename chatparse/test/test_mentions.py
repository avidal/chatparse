from .. import mentions


def test_mentions():
    """Tests that mentions are properly extracted from a variety of input"""

    cases = [
        ("@alex", ["alex"]),
        ("@alex @vidal", ["alex", "vidal"]),
        ("@a@b", ["a", "b"]),
        ("@@", []),
        ("@\"", []),
        ("""
         this is a @multi-line @mention
         let's make sure that the @regular
         expression doesn't carry over lines.
         """, ["multi-line", "mention", "regular"]),

        # XXX: Should this be valid? According to the spec it is.
        ("@123", ["123"]),
    ]

    for inp, expected in cases:
        actual = mentions.find_mentions(inp)
        assert actual == expected
