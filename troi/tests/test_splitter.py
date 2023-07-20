import unittest

from troi.splitter import DataSetSplitter, plist


class TestSplitter(unittest.TestCase):

    def test_splitter_basic(self):

        # Make invalid test set
        data = [{"score": i} for i in range(100)]
        with self.assertRaises(ValueError):
            DataSetSplitter(data, 3)

        # Now make it legal and test that
        data.reverse()  
        dss = DataSetSplitter(data, 3)
        assert dss[0][0] == {'score': 99}
        assert dss[0][-1] == {'score': 66}
        assert dss[1][0] == {'score': 65}
        assert dss[1][-1] == {'score': 33}
        assert dss[2][0] == {'score': 32}
        assert dss[2][-1] == {'score': 0}
        assert len(dss[0]) == 34
        assert len(dss[1]) == 33
        assert len(dss[2]) == 33


    def test_splitter_short(self):

        # Split and deal with empty set
        dss = DataSetSplitter([], 3)
        assert dss[0] == []
        assert dss[1] == []
        assert dss[2] == []

        dss = DataSetSplitter([{"score": 4}], 3) 
        assert dss[0] == [{'score': 4}]
        assert dss[1] == []
        assert dss[2] == []
        
        dss = DataSetSplitter([{"score": 4}, {"score": 3}], 3)
        assert dss[0] == [{'score': 4}]
        assert dss[1] == [{'score': 3}]
        assert dss[2] == []

        dss = DataSetSplitter([{"score": 4}, {"score": 3}, {"score": 2}], 3)
        assert dss[0] == [{'score': 4}]
        assert dss[1] == [{'score': 3}]
        assert dss[2] == [{'score': 2}]

        dss = DataSetSplitter([{"score": 4}, {"score": 3}, {"score": 2}, {"score": 1}], 3)
        assert dss[0] == [{'score': 4}, {'score': 3}]
        assert dss[1] == [{'score': 2}]
        assert dss[2] == [{'score': 1}]

    def test_splitter_mod_operation(self):
        dss = DataSetSplitter([{"score": 4}, {"score": 3}, {"score": 2}], 3)
        # Test the % (random item from segment)
        assert dss % 0 == {'score': 4}
        assert dss % 1 == {'score': 3}
        assert dss % 2 == {'score': 2}

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
