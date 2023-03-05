from collections import defaultdict
from datetime import datetime
from random import randint


class DataSetSplitter:

    def __init__(self, data, segment_count, field="score"):
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
                if d[self.field] > data[i-1][self.field]:
                    raise ValueError
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

        from icecream import ic
        print("segments")
        ic(self.segments)
        print("data")
        ic(self.data)

    def __getitem__(self, segment):
        return self.items(segment)

    def items(self, segment):
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

    def random_item(self, segment):
        if segment < 0 or segment >= self.segment_count:
            raise ValueError("Invalid segment")

        if len(self.segments) == 0:
            return []

        if segment == 0:
            data = self.data[0:self.segments[0]["index"]]
        else:
            data = self.data[self.segments[segment - 1]["index"]:self.segments[segment]["index"]]

        if len(data) == 0:
            return []

        return data[randint(0, len(data) - 1)]
