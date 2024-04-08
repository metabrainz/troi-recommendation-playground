import unittest

from troi import Artist, ArtistCredit, Release, Recording
import troi.operations 


class TestOperations(unittest.TestCase):

    def test_is_homogeneous(self):
        alist = [ ]
        assert troi.operations.is_homogeneous(alist) == True

        alist = [ Artist(), Artist() ]
        assert troi.operations.is_homogeneous(alist) == True

        alist = [ Artist(), Release() ]
        assert troi.operations.is_homogeneous(alist) == False

    def test_unique(self):
        # Test artists
        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        e = troi.operations.UniqueElement('mbid')
        u_alist = e.read([alist])
        assert len(u_alist) == 2

        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        e = troi.operations.UniqueElement('mbid')
        u_alist = e.read([alist])
        assert len(u_alist) == 1
        assert u_alist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'

        alist = [ ArtistCredit(artist_credit_id=65),
                  ArtistCredit(artist_credit_id=65) ]
        e = troi.operations.UniqueElement('artist_credit_id')
        u_alist = e.read([alist])
        assert len(u_alist) == 1
        assert u_alist[0].artist_credit_id == 65

        # Test recording (not testing release since rel and rec use same code)
        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        e = troi.operations.UniqueElement('foo')
        with self.assertRaises(ValueError):
            u_rlist = e.read([rlist])

        e = troi.operations.UniqueElement('mbid')
        u_rlist = e.read([rlist])
        assert len(u_rlist) == 2

        rlist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        u_rlist = e.read([rlist])
        assert len(u_rlist) == 1
        assert u_rlist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'

    def test_ensure_conformity(self):
        # Test artists
        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Artist(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        assert troi.operations._ensure_conformity(alist, blist) == True

        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Release(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        with self.assertRaises(TypeError):
            troi.operations._ensure_conformity(alist, blist)

        # Test recording (not testing release since rel and rec use same code)
        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Recording(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        assert troi.operations._ensure_conformity(alist, blist) == True

        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Release(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        with self.assertRaises(TypeError):
            troi.operations._ensure_conformity(alist, blist)

    def test_union(self):
        # Test artists
        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        blist = [ Artist(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        e = troi.operations.UnionElement()
        ulist = e.read([alist, blist])
        assert len(ulist) == 2
        assert ulist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert ulist[1].mbid == 'a1c35a51-d102-4ce7-aefb-79a361e843b6'

        # Test recording (not testing release since rel and rec use same code)
        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        blist = [ Recording(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        ulist = e.read([alist, blist])
        assert len(ulist) == 2
        assert ulist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert ulist[1].mbid == 'a1c35a51-d102-4ce7-aefb-79a361e843b6'

    def test_intersection(self):
        # Test artists
        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        e = troi.operations.IntersectionElement('meh')
        with self.assertRaises(ValueError):
            ilist = e.read([alist, blist])

        e = troi.operations.IntersectionElement('mbid')
        ilist = e.read([alist, blist])
        assert len(ilist) == 1
        assert ilist[0].mbid == blist[0].mbid

        alist = [ Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        ilist = e.read([alist, blist])
        assert len(ilist) == 0

        # Test recording (not testing release since rel and rec use same code)
        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        e = troi.operations.IntersectionElement('mbids')
        with self.assertRaises(ValueError):
            ilist = e.read([alist, blist])

        e = troi.operations.IntersectionElement('mbid')
        ilist = e.read([alist, blist])
        assert len(ilist) == 1
        assert ilist[0].mbid == blist[0].mbid

        alist = [ Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        ilist = e.read([alist, blist])
        assert len(ilist) == 0

    def test_difference(self):
        # Test artists
        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        e = troi.operations.DifferenceElement('mbids')
        with self.assertRaises(ValueError):
            ilist = e.read([alist, blist])

        e = troi.operations.DifferenceElement('mbid')
        ilist = e.read([alist, blist])
        assert len(ilist) == 1
        assert ilist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'

        alist = [ Artist(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Artist(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Artist(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        dlist = e.read([alist, blist])
        assert len(dlist) == 2
        assert dlist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert dlist[1].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'

        # Test recording (not testing release since rel and rec use same code)
        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd') ]
        e = troi.operations.DifferenceElement('mbids')
        with self.assertRaises(ValueError):
            ilist = e.read([alist, blist])

        e = troi.operations.DifferenceElement('mbid')
        ilist = e.read([alist, blist])
        assert len(ilist) == 1
        assert ilist[0].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'

        alist = [ Recording(mbid='8756f690-18ca-488d-a456-680fdaf234bd'), 
                  Recording(mbid='73a9d0db-0ec7-490e-9a85-0525a5ccef8e') ]
        blist = [ Recording(mbid='a1c35a51-d102-4ce7-aefb-79a361e843b6') ]
        dlist = e.read([alist, blist])
        assert len(dlist) == 2
        assert dlist[0].mbid == '8756f690-18ca-488d-a456-680fdaf234bd'
        assert dlist[1].mbid == '73a9d0db-0ec7-490e-9a85-0525a5ccef8e'
