import unittest

from troi import Artist, Recording
import troi.sorts 


class TestYearSortElement(unittest.TestCase):

    def test_year_sort_element(self):
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd', year=1980), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e', year=1970),
                  Recording(mbid='07316967-cfcb-4920-b8ca-e96dcb4afc08'),
                  Recording(mbid='88b433b3-2c4f-4c8b-839b-77a203ec950f', year=1990) ]

        e = troi.sorts.YearSortElement()
        flist = e.read([rlist])
        assert len(flist) == 4
        assert flist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
        assert flist[1].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[2].mbid == '88b433b3-2c4f-4c8b-839b-77a203ec950f'
        assert flist[3].mbid == '07316967-cfcb-4920-b8ca-e96dcb4afc08'

        e = troi.sorts.YearSortElement(reverse=True)
        flist = e.read([rlist])
        assert len(flist) == 4
        assert flist[0].mbid == '07316967-cfcb-4920-b8ca-e96dcb4afc08'
        assert flist[1].mbid == '88b433b3-2c4f-4c8b-839b-77a203ec950f'
        assert flist[2].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert flist[3].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
