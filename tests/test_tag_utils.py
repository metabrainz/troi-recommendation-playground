from troi.content_resolver.formats.tag_utils import extract_track_number


class TestTagUtils:

    def test_int(self):
        assert extract_track_number(100) == 100
        assert extract_track_number(-100) == -100

    def test_string(self):
        assert extract_track_number("100") == 100

    def test_string_with_slash(self):
        assert extract_track_number("9/12") == 9

    def test_invalid_values(self):
        assert extract_track_number(None) == None
        assert extract_track_number("") == None
        assert extract_track_number("NotANumber") == None
        assert extract_track_number("3.0") == None
