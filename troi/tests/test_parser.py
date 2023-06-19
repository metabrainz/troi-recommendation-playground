import unittest

from troi.parse_prompt import parse, ParseError


class TestParser(unittest.TestCase):

    def test_basic_entities(self):
        r, _ = parse("a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "artist", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "artist", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("r:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "recording", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("recording:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "recording", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("rl:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "release", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("release:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "release", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("rg:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "release-group", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("release-group:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "release-group", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("g:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "genre", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("c:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "country", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("country:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "country", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("ar:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "area", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        r, _ = parse("area:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == { "entity": "area", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "args": None }

        self.assertRaises(ParseError, parse, "wrong:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")

    def test_tags(self):

        r, _ = parse("t:abstract t:rock t:blues")
        assert r[0] == { "entity": "tag", "values": ["abstract"], "args": None }
        assert r[1] == { "entity": "tag", "values": ["rock"], "args": None }
        assert r[2] == { "entity": "tag", "values": ["blues"], "args": None }

        r, _ = parse("t:(abstract rock blues)")
        assert r[0] == { "entity": "tag", "values": ["abstract", "rock", "blues"], "args": None }

        r, _ = parse("t:(abstract rock blues):or")
        assert r[0] == { "entity": "tag", "values": ["abstract", "rock", "blues"], "args": "or" }
        r, _ = parse("t:(abstract rock blues):and")
        assert r[0] == { "entity": "tag", "values": ["abstract", "rock", "blues"], "args": "and" }
        self.assertRaises(ParseError, parse, "t:(abstract rock blues):bork")

        self.assertRaises(ParseError, parse, "tag:(foo")
        self.assertRaises(ParseError, parse, "tag:foo)")

        r, _ = parse('t:("trip hop" "hip hop")')
        assert r[0] == { "entity": "tag", "values": ["trip hop", "hip hop"], "args": None }

        self.assertRaises(ParseError, parse, 'tag:foo"')
        self.assertRaises(ParseError, parse, 'tag:"foo')

    def test_shortcuts(self):
        r, _ = parse("#abstract #rock #blues")
        assert r[0] == { "entity": "tag", "values": ["abstract"], "args": None }
        assert r[1] == { "entity": "tag", "values": ["rock"], "args": None }
        assert r[2] == { "entity": "tag", "values": ["blues"], "args": None }

    def test_years(self):
        r, _ = parse("y:1984 year:1989")
        assert r[0] == { "entity": "year", "values": [1984], "args": None }
        assert r[1] == { "entity": "year", "values": [1989], "args": None }

        r, _ = parse("ys:1984-1989")
        assert r[0] == { "entity": "years", "values": [1984, 1989], "args": None }

    # test compound statements
