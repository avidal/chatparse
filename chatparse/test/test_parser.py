from .. import parse


def test_example_cases():

    cases = [
        ("@chris you around?",
         {
             "mentions": ["chris"]
         }
        ),

        ("Good morning! (megusta) (coffee)",
         {
             "emoticons": ["megusta", "coffee"]
         }
        ),

        ("Olympics are starting soon; http://www.nbcolympics.com",
         {
             "links": [{
                 "url": u"http://www.nbcolympics.com",
                 "title": "NBC Olympics | Home of the 2016 Olympic Games in Rio"
             }]
         }
        ),

        ("@bob @john (success) such a cool feature; https://twitter.com/jdorfman/status/430511497475670016",
         {
             "mentions": ["bob", "john"],
             "emoticons": ["success"],
             "links": [{
                "url": u"https://twitter.com/jdorfman/status/430511497475670016",
                "title": 'Justin Dorfman on Twitter: "nice @littlebigdetail from @HipChat (shows hex colors when pasted in chat). http://t.co/7cI6Gjy5pq"'
            }]
         }
        ),
    ]

    for inp, expected in cases:
        actual = parse(inp, as_json=False)
        assert actual == expected
