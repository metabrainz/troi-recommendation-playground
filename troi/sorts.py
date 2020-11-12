from operator import attrgetter

import troi
from troi import PipelineError, Recording


class YearSortElement(troi.Element):
    '''
        Sort recordings by year.
    '''

    def __init__(self, reverse=False):
        '''
            Sort recordings by year ascending. If reverse=True, sort descending.
        '''
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
                return 0
            return r.year

        return sorted(inputs[0], key=year_sorter, reverse=self.reverse)
