from collections import defaultdict
from datetime import datetime
from random import randint


class DataSetSplitter:
    """
        The data set splitter is a tool that can take descendingly
        ordered lists of dicts. Given a number of segments, it 
        provides easy to use accessor functions for quick access
        to the various sections of the data.

        This tool is useful for taking data sets that are
        ordered by some key and breaking them into chunks based
        on the field used to sort the data. By default it is 
        "score", but can be overriden with the field argument.

        The class will scan all the rows in the data and examine
        the key field (e.g. "score") and determine the splits
        based on the score, so that the segments split equally
        according to score. This very likely means that the
        different segments will contain a different number of
        items, unless you data scores are perfectly linear.

        This class keeps a reference to your data set, but it
        never modifies the underlying data, it only ever returns
        sections of the data.

        Array indexing is possible to access each slice: 

           dss = DataSetSplitter(data, 3)
           first_segment = dss[0]

        % for returning a random item from a segment is possible:

           random_item = dss % 1

        This will return one random item from segment 1.

    """

    def __init__(self, data, segment_count, field="score"):
        """
            Pass in the descendingly sorted data, keyed by the
            field (default "score") and a segment count for
            the number of segments to break this dataset into.
        """
        self.segment_count = segment_count
        self.field = field

        if len(data) == 0:
            self.segments = []
            return
        self.data = data

        high_score = data[0][self.field]
        low_score = data[-1][self.field]

        # Calculate where the segments breaks should be from how to hi
        segment_width = (high_score - low_score) / self.segment_count
        self.segments = []
        for segment in range(self.segment_count):
            self.segments.append({self.field: low_score + ((self.segment_count - 1) - segment) * segment_width})

        # translate the breaks into actual indexes in the data
        segment_index = 0
        count = 0
        for i, d in enumerate(data):

            # Test to ensure that the data is in descending order
            if i > 0:
                if d[self.field] > data[i - 1][self.field]:
                    raise ValueError("Data set is not in descending order!")
            if d[self.field] < self.segments[segment_index][self.field]:
                self.segments[segment_index]["index"] = i - 1
                self.segments[segment_index]["count"] = count
                segment_index += 1
                count = 0

            count += 1

        # Finish off the data set and accont for special (short) data sets
        for i in range(segment_index, segment_count):
            if count > 0:
                self.segments[i]["index"] = len(data) - 1
                self.segments[i]["count"] = count
                count = 0
            else:
                self.segments[i]["index"] = None
                self.segments[i]["count"] = 0

    def get_segment_count(self):
        return self.segment_count

    def __getitem__(self, segment):
        """ 
            Array indexing for access to the segments. See method items().
        """
        return self.items(segment)

    def items(self, segment):
        """
            Return a list of all of the items in the specified segment.
            If an invalid segment is specified, a ValueError will be thrown.
        """
        if segment < 0 or segment >= self.segment_count:
            raise ValueError("Invalid segment")

        if len(self.segments) == 0:
            return []

        try:
            if segment == 0:
                return self.data[0:self.segments[0]["index"] + 1]
            else:
                return self.data[self.segments[segment - 1]["index"] + 1:self.segments[segment]["index"] + 1]
        except TypeError:
            # Type error catches when a None value is being used in the index math
            return []

    def __mod__(self, segment):
        """
            Use % operator to return a random item from segment. See random_item()

        """
        return self.random_item(segment)

    def random_item(self, segment, count=1):
        """
            Return a random item from the specified segment. 

            count specifies the number of items to return, default 1.

            Return value is a data item, unless count is > 1, then a list is returned
        """
        if segment < 0 or segment >= self.segment_count:
            raise ValueError("Invalid segment")

        if len(self.segments) == 0:
            return []

        data = self.items(segment)
        items = [data[randint(0, len(data) - 1)] for i in range(min(count, len(data)))]
        items = [dict(t) for t in {tuple(d.items()) for d in items}]

        if count > 1:
            return items

        return items[0] if len(items) > 0 else []

    def random(self):
        """
            Return the data from a random segment.
            NOTE: To return a random item, use random_item or the % operator.
        """
        if len(self.segments) == 0:
            return []

        segment = randint(0, len(self.segments))
        return self.items(segment)


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
        items = [data[randint(0, len(data) - 1)] for i in range(min(count, len(data)))]
        if count > 1:
            return items

        return items[0] if len(items) > 0 else []
