from uuid import UUID
import unittest

from troi.parse_prompt import PromptParser, ParseError


class TestParser(unittest.TestCase):

    def test_basic_entities(self):
        pp = PromptParser()
        r = pp.parse("artist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        r = pp.parse("artist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        self.assertRaises(ParseError, pp.parse, "wrong:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")
        self.assertRaises(ParseError, pp.parse, "artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")

        r = pp.parse("artist:(the knife)")
        assert r[0] == {"entity": "artist", "values": ["the knife"], "weight": 1, "opts": []}

        self.assertRaises(ParseError, pp.parse, "artist:u2:nosim")
        self.assertRaises(ParseError, pp.parse, "artists:u2:nosim")
        self.assertRaises(ParseError, pp.parse, "country:andorra")

    def test_tags(self):
        pp = PromptParser()
        r = pp.parse("tag:abstract tag:rock tag:blues")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": 1, "opts": []}
        assert r[1] == {"entity": "tag", "values": ["rock"], "weight": 1, "opts": []}
        assert r[2] == {"entity": "tag", "values": ["blues"], "weight": 1, "opts": []}

        r = pp.parse("tag:(abstract,rock,blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": []}

        r = pp.parse("tag:(abstract rock blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract rock blues"], "weight": 1, "opts": []}

        r = pp.parse("tag:(abstract,rock,blues):1:or")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": ["or"]}
        r = pp.parse("tag:(abstract,rock,blues)")
        assert r[0] == {"entity": "tag", "values": ["abstract", "rock", "blues"], "weight": 1, "opts": []}

        r = pp.parse('tag:(trip hop, hip hop)')
        assert r[0] == {"entity": "tag", "values": ["trip hop", "hip hop"], "weight": 1, "opts": []}

        r = pp.parse("tag:(r&b)")
        assert r[0] == {"entity": "tag", "values": ["r&b"], "weight": 1, "opts": []}

        r = pp.parse("tag:(blümchen)")
        assert r[0] == {"entity": "tag", "values": ["blümchen"], "weight": 1, "opts": []}

        r = pp.parse("tag:(モーニング娘。)")
        assert r[0] == {"entity": "tag", "values": ["モーニング娘。"], "weight": 1, "opts": []}

        r = pp.parse("tag:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "tag", "values": ["57baa3c6-ee43-4db3-9e6a-50bbc9792ee4"], "weight": 1, "opts": []}

    def test_tag_errors(self):
        pp = PromptParser()
        self.assertRaises(ParseError, pp.parse, "t:(abstract rock blues):bork")
        self.assertRaises(ParseError, pp.parse, "tag:(foo")
        self.assertRaises(ParseError, pp.parse, "tag:foo)")

    def test_shortcuts(self):
        pp = PromptParser()
        r = pp.parse("#abstract")
        assert r[0] == {"entity": "tag", "values": ["abstract"], "weight": 1, "opts": []}

        pp = PromptParser()
        r = pp.parse("u2")
        assert r[0] == {"entity": "artist", "values": ["u2"], "weight": 1, "opts": []}

        pp = PromptParser()
        r = pp.parse("amy winehouse")
        assert r[0] == {"entity": "artist", "values": ["amy winehouse"], "weight": 1, "opts": []}

    def test_compound(self):
        pp = PromptParser()
        r = pp.parse('artist:(05319f96-e409-4199-b94f-3cabe7cc188a):2 tag:(downtempo):1 tag:(trip hop, abstract):2')
        assert r[0] == {"entity": "artist", "values": [UUID("05319f96-e409-4199-b94f-3cabe7cc188a")], "weight": 2, "opts": []}
        assert r[1] == {"entity": "tag", "values": ["downtempo"], "weight": 1, "opts": []}
        assert r[2] == {"entity": "tag", "values": ["trip hop", "abstract"], "weight": 2, "opts": []}

    def test_weights(self):
        pp = PromptParser()
        r = pp.parse("artist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4):1 artist:(f54ba4c6-12dd-4358-9136-c64ad89420c5):2")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}
        assert r[1] == {"entity": "artist", "values": [UUID("f54ba4c6-12dd-4358-9136-c64ad89420c5")], "weight": 2, "opts": []}

        self.assertRaises(ParseError, pp.parse,
                          "artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 artist:f54ba4c6-12dd-4358-9136-c64ad89420c5:fussy")
        self.assertRaises(ParseError, pp.parse, "artist:57baa3c6-ee43-4db3-9e6a-50bbc9792ee4:1 artist:f54ba4c6-12dd-4358-9136-c64ad89420c5:.5")

        r = pp.parse("artist:(portishead)::easy")
        assert r[0] == {"entity": "artist", "values": ["portishead"], "weight": 1, "opts": ["easy"]}

        r = pp.parse("artist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)::easy")
        assert r[0] == {"entity": "artist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": ["easy"]}

    def test_opts(self):
        pp = PromptParser()
        r = pp.parse("stats:(mr_monkey)::month")
        print(r[0])
        assert r[0] == {"entity": "stats", "values": ["mr_monkey"], "weight": 1, "opts": ["month"]}
        r = pp.parse("artist:(monkey)::nosim,easy")
        assert r[0] == {"entity": "artist", "values": ["monkey"], "weight": 1, "opts": ["nosim", "easy"]}

        self.assertRaises(ParseError, pp.parse, 'artist:(meh)::nosim,')

    def test_parens(self):
        pp = PromptParser()
        self.assertRaises(ParseError, pp.parse, 'artist:adfadf(meh)')
        self.assertRaises(ParseError, pp.parse, 'artist:adfadf(meh')
        self.assertRaises(ParseError, pp.parse, 'artist:adfadf)meh')

    def test_collection_playlist(self):
        pp = PromptParser()
        r = pp.parse("collection:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "collection", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        r = pp.parse("playlist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "playlist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        r = pp.parse("playlist:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "playlist", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

    def test_stats(self):
        pp = PromptParser()
        r = pp.parse("stats:mr_monkey:1:year")
        assert r[0] == {"entity": "stats", "values": ["mr_monkey"], "weight": 1, "opts": ["year"]}

        r = pp.parse("stats:rob:1:week")
        assert r[0] == {"entity": "stats", "values": ["rob"], "weight": 1, "opts": ["week"]}

        r = pp.parse("stats:(mr_monkey)::month")
        assert r[0] == {"entity": "stats", "values": ["mr_monkey"], "weight": 1, "opts": ["month"]}

        r = pp.parse("stats:(mr_monkey):2:month")
        assert r[0] == {"entity": "stats", "values": ["mr_monkey"], "weight": 2, "opts": ["month"]}

        r = pp.parse("stats:(rob zombie)")
        assert r[0] == {"entity": "stats", "values": ["rob zombie"], "weight": 1, "opts": []}

    def test_recs(self):
        pp = PromptParser()
        self.assertRaises(ParseError, pp.parse, 'recs:')

        r = pp.parse("recs:mr_monkey::listened")
        assert r[0] == {"entity": "recs", "values": ["mr_monkey"], "weight": 1, "opts": ["listened"]}

        r = pp.parse("recs:rob:1:unlistened")
        assert r[0] == {"entity": "recs", "values": ["rob"], "weight": 1, "opts": ["unlistened"]}

        r = pp.parse("recs:(mr_monkey):1:listened")
        assert r[0] == {"entity": "recs", "values": ["mr_monkey"], "weight": 1, "opts": ["listened"]}

        r = pp.parse("recs:(mr_monkey):2:unlistened")
        assert r[0] == {"entity": "recs", "values": ["mr_monkey"], "weight": 2, "opts": ["unlistened"]}

        r = pp.parse("recs:(rob zombie)")
        assert r[0] == {"entity": "recs", "values": ["rob zombie"], "weight": 1, "opts": []}

    def test_country(self):
        pp = PromptParser()
        r = pp.parse("country:(57baa3c6-ee43-4db3-9e6a-50bbc9792ee4)")
        assert r[0] == {"entity": "country", "values": [UUID("57baa3c6-ee43-4db3-9e6a-50bbc9792ee4")], "weight": 1, "opts": []}

        r = pp.parse("country:(mali)")
        assert r[0] == {"entity": "country", "values": ["mali"], "weight": 1, "opts": []}
