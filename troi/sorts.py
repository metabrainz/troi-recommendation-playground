from sys import maxsize
from operator import attrgetter

import troi
from troi import PipelineError, Recording


class YearSortElement(troi.Element):
    '''
        Sort recordings by year ascending -- recordings that have the same
        year will be returned in an undefined order. Recordings
        that have no year set will be returned at the end of the list.
        If reverse=True, sort descending and return tracks with no year
        first.

        :param reverse: Reverse the sort order.
    '''

    def __init__(self, reverse=False):
        super().__init__()
        self.reverse = reverse

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        def year_sorter(r):
            if not r.year:
                return maxsize
            return r.year

        return sorted(inputs[0], key=year_sorter, reverse=self.reverse)
