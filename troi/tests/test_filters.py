import unittest

from troi import Artist, Recording
import troi.filters 


class TestArtistCreditFilterElement(unittest.TestCase):

    def test_artist_credit_filter_include(self):
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist=Artist(artist_credit_id=65)), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist=Artist(artist_credit_id=197)) ]
        alist = [ 197 ]

        e = troi.filters.ArtistCreditFilterElement(alist, include=True)
        flist = e.read([rlist])
        assert len(flist) == 1
        assert flist[0].artist.artist_credit_id == 197
        assert flist[0].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"

        alist = [ 1 ]
        e = troi.filters.ArtistCreditFilterElement(alist, include=True)
        flist = e.read([rlist])
        assert len(flist) == 0

    def test_artist_credit_filter_exclude(self):
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist=Artist(artist_credit_id=65)), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist=Artist(artist_credit_id=197)) ]
        alist = [ 197 ]

        e = troi.filters.ArtistCreditFilterElement(alist)
        flist = e.read([rlist])
        assert len(flist) == 1
        assert flist[0].artist.artist_credit_id == 65
        assert flist[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"

        alist = [ 1 ]
        e = troi.filters.ArtistCreditFilterElement(alist)
        flist = e.read([rlist])
        assert len(flist) == 2


class TestArtistCreditLimiterElement(unittest.TestCase):
    def test_artist_credit_limiter_higher_ranked(self):
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist=Artist(artist_credit_id=65), ranking=1.0), 
                  Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', artist=Artist(artist_credit_id=65), ranking=.5), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist=Artist(artist_credit_id=197), ranking=.1) ]

        e = troi.filters.ArtistCreditLimiterElement(1)
        flist = e.read([rlist])
        assert len(flist) == 2
        assert flist[0].artist.artist_credit_id == 65
        assert flist[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"
        assert flist[1].artist.artist_credit_id == 197
        assert flist[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"

        e = troi.filters.ArtistCreditLimiterElement(1, exclude_lower_ranked=False)
        flist = e.read([rlist])
        assert len(flist) == 2
        assert flist[0].artist.artist_credit_id == 65
        assert flist[0].mbid == "139654ae-2c02-4e0f-aee0-c47da6e59ff1"
        assert flist[1].artist.artist_credit_id == 197
        assert flist[1].mbid == "73a9d0db-0ec7-490e-9a85-0525a5ccef8e"


class TestDuplicateRecordingFilterElement(unittest.TestCase):
    def test_duplicate_recording_filter_element(self):
        rlist = [Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
                 Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1')]
        e = troi.filters.DuplicateRecordingFilterElement()
        flist = e.read([rlist])
        assert len(flist) == 3

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'
        assert flist[2].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'


class TestConsecutiveRecordingFilterElement(unittest.TestCase):
    def test_consecutive_recording_filter_element(self):
        rlist = [Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1'),
                 Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'),
                 Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
                 Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e'),
                 Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1')]
        e = troi.filters.ConsecutiveRecordingFilterElement()
        flist = e.read([rlist])
        assert len(flist) == 5

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'
        assert flist[2].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[3].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
        assert flist[4].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'


class TestYearRangeFilterElement(unittest.TestCase):
    def test_year_range_filter_element(self):
        rlist = [Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', year=1980),
                 Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', year=1990),
                 Recording(mbid='139654ae-2c02-4e0f-aee0-c47da6e59ff1', year=2000)]
        e = troi.filters.YearRangeFilterElement(1985, 1995)
        flist = e.read([rlist])
        assert len(flist) == 1

        assert flist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'

        e = troi.filters.YearRangeFilterElement(1985, 1995, inverse=True)
        flist = e.read([rlist])
        assert len(flist) == 2

        assert flist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[1].mbid == '139654ae-2c02-4e0f-aee0-c47da6e59ff1'
