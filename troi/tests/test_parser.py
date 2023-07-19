from uuid import UUID 
import unittest

from troi.parse_prompt import parse, ParseError


class TestParser(unittest.TestCase):

    def test_basic_entities(self):
        r = parse("a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        r = parse("artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        self.assertRaises(ParseError, parse, "wrong:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")

    def test_tags(self):

        r = parse("t:abstract t:rock t:blues")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": 1, "opts": []}
        assert r[1] == {"entity": "tag", "values": ["rock"], "weight": 1, "opts": []}
        assert r[2] == {"entity": "tag", "values": ["blues"], "weight": 1, "opts": []}

        r = parse("t:(abstract,rock,blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": []}

        r = parse("t:(abstract rock blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract rock blues"], "weight": 1, "opts": []}

        r = parse("tag:(abstract,rock,blues):1:or")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": ["or"]}
        r = parse("t:(abstract,rock,blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": []}

        r = parse('t:(trip hop, hip hop)')
        assert r[0] == {"entity": "tag", "values": ["trip hop", "hip hop"], "weight": 1, "opts": []}

        r = parse("t:(r&b)")
        assert r[0] == {"entity": "tag", "values": ["r&b"], "weight": 1, "opts": []}

        r = parse("t:r&b")
        assert r[0] == {"entity": "tag", "values": ["r&b"], "weight": 1, "opts": []}

    def test_tag_errors(self):
        self.assertRaises(ParseError, parse, "t:(abstract rock blues):bork")
        self.assertRaises(ParseError, parse, "tag:(foo")
        self.assertRaises(ParseError, parse, "tag:foo)")
        self.assertRaises(ParseError, parse, 'tag:foo"')
        self.assertRaises(ParseError, parse, 'tag:"foo')

    def test_shortcuts(self):
        r = parse("#abstract #rock #blues")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": 1, "opts": []}
        assert r[1] == {"entity": "tag", "values": ["rock"], "weight": 1, "opts": []}
        assert r[2] == {"entity": "tag", "values": ["blues"], "weight": 1, "opts": []}

    def test_compound(self):
        r = parse(
            'artist:05319f96-e409-4199-b94f-3cabe7cc188a:2 #downtempo:1 tag:(trip hop, abstract):2'
        )
        assert r[0] == {"entity": "artist", "values": [UUID("05319f96-e409-4199-b94f-3cabe7cc188a")], "weight": 2, "opts": []}
        assert r[1] == {"entity": "tag", "values": ["downtempo"], "weight": 1, "opts": []}
        assert r[2] == {"entity": "tag", "values": ["trip hop", "abstract"], "weight": 2, "opts": []}

    def test_weights(self):
        r = parse("a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:2")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}
        assert r[1] == {"entity": "artist", "values": [UUID("f54ba4c6-12dd-4358-9136-c64ad89420c5")], "weight": 2, "opts": []}

        self.assertRaises(ParseError, parse,
                          "a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:fussy")
        self.assertRaises(ParseError, parse, "a:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 a:f54ba4c6-12dd-4358-9136-c64ad89420c5:.5")

    def test_hated_liked(self):

        r = parse("hated:2")
        assert r[0] == {"entity": "hated", "values": ["2"], "weight": 1, "opts": []}

        r = parse("liked:2")
        assert r[0] == {"entity": "liked", "values": ["2"], "weight": 1, "opts": []}
