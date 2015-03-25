from .. import emoticons


def test_emoticons():

    cases = [
        ("(thumbsup)", ['thumbsup']),
        ("(good)(for)(you)", ['good', 'for', 'you']),
        ("Good morning! (megusta) (coffee)", ['megusta', 'coffee']),
        ("(nested (emoticon))", ["emoticon"]),
        ("(a)", ['a']),
        ("(no-hyphens-allowed)", []),
        ("()", []),
        ('("quoted")', []),
    ]

    for inp, expected in cases:
        actual = emoticons.find_emoticons(inp)
        assert actual == expected
