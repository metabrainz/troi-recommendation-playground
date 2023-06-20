import unittest

from troi.parse_prompt import parse, ParseError


class TestParser(unittest.TestCase):

    def test_basic_entities(self):
        r = parse("a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "artist", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "artist", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("r:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "recording", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("recording:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "recording", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("rl:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "release", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("release:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "release", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("rg:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "release-group", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("release-group:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "release-group", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("g:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "genre", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("c:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "country", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("country:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "country", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("ar:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "area", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        r = parse("area:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "area", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": None}

        self.assertRaises(ParseError, parse, "wrong:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")

    def test_tags(self):

        r = parse("t:abstract t:rock t:blues")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": None}
        assert r[1] == {"entity": "tag", "values": ["rock"], "weight": None}
        assert r[2] == {"entity": "tag", "values": ["blues"], "weight": None}

        r = parse("t:(abstract rock blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": None}

        r = parse("to:(abstract rock blues)")
        assert r[0] == {"entity": "tag-or", "values": ["abstract", "rock", "blues"], "weight": None}
        r = parse("tag-or:(abstract rock blues)")
        assert r[0] == {"entity": "tag-or", "values": ["abstract", "rock", "blues"], "weight": None}
        r = parse("t:(abstract rock blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": None}

        r = parse('t:("trip hop" "hip hop")')
        assert r[0] == {"entity": "tag", "values": ["trip hop", "hip hop"], "weight": None}

    def test_tag_errors(self):
        self.assertRaises(ParseError, parse, "t:(abstract rock blues):bork")
        self.assertRaises(ParseError, parse, "tag:(foo")
        self.assertRaises(ParseError, parse, "tag:foo)")
        self.assertRaises(ParseError, parse, 'tag:foo"')
        self.assertRaises(ParseError, parse, 'tag:"foo')

    def test_shortcuts(self):
        r = parse("#abstract #rock #blues")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": None}
        assert r[1] == {"entity": "tag", "values": ["rock"], "weight": None}
        assert r[2] == {"entity": "tag", "values": ["blues"], "weight": None}

    def test_years(self):
        r = parse("y:1984 year:1989")
        assert r[0] == {"entity": "year", "values": [1984], "weight": None}
        assert r[1] == {"entity": "year", "values": [1989], "weight": None}

        r = parse("ys:1984-1989")
        assert r[0] == {"entity": "years", "values": [1984, 1989], "weight": None}

    def test_compound(self):
        r = parse(
            'artist:05319f96-e409-4199-b94f-3cabe7cc188a:2 #downtempo:1 tag:("trip hop" abstract):2 c:d1ad6d63-448b-43c7-9de3-e60ac8418106 y:1996 ys:1986-2000'
        )
        assert r[0] == {"entity": "artist", "values": ["05319f96-e409-4199-b94f-3cabe7cc188a"], "weight": 2}
        assert r[1] == {"entity": "tag", "values": ["downtempo"], "weight": 1}
        assert r[2] == {"entity": "tag", "values": ["trip hop", "abstract"], "weight": 2}
        assert r[3] == {"entity": "country", "values": ["d1ad6d63-448b-43c7-9de3-e60ac8418106"], "weight": None}
        assert r[4] == {"entity": "year", "values": [1996], "weight": None}
        assert r[5] == {"entity": "years", "values": [1986, 2000], "weight": None}

    def test_weights(self):
        r = parse("a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:2")
        assert r[0] == {"entity": "artist", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": 1}
        assert r[1] == {"entity": "artist", "values": ["f54ba4c6-12dd-4358-9136-c64ad89420c5"], "weight": 2}

        self.assertRaises(ParseError, parse,
                          "a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:fussy")
        self.assertRaises(ParseError, parse, "a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:.5")
