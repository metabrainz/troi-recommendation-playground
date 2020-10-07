import os
import unittest

from troi import Artist, Release, Recording
import troi.operations 


class TestOperations(unittest.TestCase):

    def test_artist_credit_filter(self):
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', artist=Artist(artist_credit_id=65)), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', artist=Artist(artist_credit_id=197)) ]
        alist = [ Artist(artist_credit_id=65) ]

        e = troi.operations.ArtistCreditFilterElement()
        flist = e.read([rlist, alist])
        assert len(flist) == 1
        assert flist[0].artist.artist_credit_id == 65
        assert flist[0].mbid == "8756f690-18ca-488d-a456-680fdaf234bd"

        alist = [ Artist(artist_credit_id=1) ]
        flist = e.read([rlist, alist])
        assert len(flist) == 0
