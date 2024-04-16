from collections import defaultdict
import troi
from random import randint
from troi import Recording
from troi import TARGET_NUMBER_OF_RECORDINGS


class InterleaveRecordingsElement(troi.Element):
    """
        This element round-robins the various input sources into one list until all sources are all empty.
    """

    def __init__(self):
        troi.Element.__init__(self)

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, entities):

        recordings = []
        while True:
            empty = 0
            for entity in entities:
                try:
                    recordings.append(entity.pop(0))
                except IndexError:
                    empty += 1

            # Did we process all the recordings?
            if empty == len(entities):
                break

        return recordings


class WeighAndBlendRecordingsElement(troi.Element):
    """
        This element will weight all the given sources according to weights passed to __init__ and
        then combine all the input sources into one weighted output stream.

        A source that has a weight of 2 will be chosen 2 times more often than a source with weight 1.
    """

    def __init__(self, weights, max_num_recordings=TARGET_NUMBER_OF_RECORDINGS, max_artist_occurrence=None):
        troi.Element.__init__(self)
        self.weights = weights
        self.max_num_recordings = max_num_recordings
        self.max_artist_occurrence = max_artist_occurrence

    def inputs(self):
        return [Recording]

    def outputs(self):
        return [Recording]

    def read(self, entities):

        total_available = sum([len(e) for e in entities])

        # prepare the weights
        total = sum(self.weights)
        summed = []
        acc = 0
        for i in self.weights:
            acc += i
            summed.append(acc)

        # Ensure seed artists are the first tracks -- doing this for all recording elements work in this case.
        recordings = []
        for element in entities:
            try:
                recordings.append(element.pop(0))
            except IndexError:
                pass

        # This still allows sequential tracks to be from the same artists. I'll wait for feedback to see if this
        # is a problem.
        artist_counts = defaultdict(int)
        dedup_set = set()
        while True:
            r = randint(0, total)
            for i, s in enumerate(summed):
                if r < s:
                    while True:
                        if len(entities[i]) > 0:
                            rec = entities[i].pop(0)
                            if rec.mbid in dedup_set:
                                total_available -= 1
                                continue
                            if self.max_artist_occurrence is not None and \
                                    artist_counts[rec.artist_credit.artist_credit_id] == self.max_artist_occurrence:
                                total_available -= 1
                                continue

                            recordings.append(rec)
                            dedup_set.add(rec.mbid)
                            artist_counts[rec.artist_credit.artist_credit_id] += 1
                        break

            if len(recordings) >= self.max_num_recordings or len(recordings) == total_available:
                break

        return recordings
