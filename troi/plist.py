from collections import defaultdict
from datetime import datetime
from random import randint


class plist(list):
    """ 
        This class implements a list object with percent based indexing and slicing:

        > a = plist((1,2,3,4))
        > a[50:]
        [3, 4]
        > a[25:75]
        [2, 3]
       
        Also supported are slicing on unit interval, using the uslice function:
        > a[a.uslice(.5)
        [3, 4]

    """

    def _get_index(self, percent):
        if len(self) == 0:
            return None

        if percent is not None:
            if isinstance(percent, int):
                if percent < 0 or percent > 100:
                    raise ValueError("Percent must be between 0 and 100.")
                return percent * len(self) // 100
            elif isinstance(percent, float):
                return int(percent * len(self))
            else:
                raise ValueError("percent must be an int or float.")
        else:
            return None

    def __getitem__(self, percent):

        if isinstance(percent, slice):
            start = self._get_index(percent.start)
            stop = self._get_index(percent.stop)
            return super().__getitem__(slice(self._get_index(percent.start), self._get_index(percent.stop)))
        else:
            return super().__getitem__(self._get_index(percent))

    def uslice(self, start_percent=None, stop_percent=None):

        if start_percent is None and stop_percent is None:
            raise IndexError("Invalid slice arguments. Must be at least one integer or float.")

        start_index = self._get_index(start_percent)
        stop_index = self._get_index(stop_percent)

        return super().__getitem__(slice(start_index, stop_index))

    def dslice(self, start=None, stop=None):
        return super().__getitem__(slice(start, stop))

    def random_item(self, start_percent=0, stop_percent=99, count=1):
        """
            Return a random item from the specified percent slice

            count specifies the number of items to return, default 1.

            Return value is a data item, unless count is > 1, then a list is returned
        """

        if len(self) == 0:
            return []

        start_index = self._get_index(start_percent)
        stop_index = self._get_index(stop_percent)

        data = super().__getitem__(slice(start_index, stop_index))
        items = []
        for i in range(len(data)):
            index = randint(0, len(data) - 1)
            items.append(data[index])
            del data[index]
            if len(items) == count or not data:
                break

        if count > 1:
            return items
        else:
            return items[0] if len(items) > 0 else []
