import os
import unittest

from troi import Artist, Release, Recording
import troi.filters 


class TestFilters(unittest.TestCase):

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
