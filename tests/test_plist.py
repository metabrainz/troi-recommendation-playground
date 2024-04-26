import unittest

from troi.plist import plist


class TestSplitter(unittest.TestCase):

    def test_plist(self):
        pl = plist([0,1,2,3,4,5,6,7,8,9])

        assert pl[0:10] == [0]
        assert pl[0:20] == [0,1]
        assert pl[50:100] == [5,6,7,8,9]
        assert pl.uslice(0, 10) == [0]
        assert pl.uslice(0, 20) == [0,1]
        assert pl.uslice(50, 100) == [5,6,7,8,9]

        assert pl.dslice(0, 2) == [0,1]

        assert pl.random_item(50, 100) in [5,6,7,8,9]

    def test_plist_unique(self):
        pl = plist([0,1,2,3,4,5,6,7,8,9])
        rlist = pl.random_item(count=9)
        assert len(rlist) == len(set(rlist))
