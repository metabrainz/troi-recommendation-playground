import requests

from troi import Element, Artist, PipelineError, Recording


def chunks(lst, n):
    """ Break a list into roughly equally spaced chunks """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class MoodLookupElement(Element):
    '''
    '''

    SERVER_URL = "http://acousticbrainz.org/api/v1/high-level?recording_ids="

    def __init__(self, skip_not_found=True):
        Element.__init__(self)
        self.skip_not_found = skip_not_found

    @staticmethod
    def inputs():
        return [ Recording ]

    @staticmethod
    def outputs():
        return [ Recording ]


    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        max_items_per_call = 25
        for rec_chunk in chunks(recordings, max_items_per_call):
            mbids = [ r.mbid for r in rec_chunk ]
            r = requests.post(self.SERVER_URL + ";".join(mbids))
            if r.status_code != 200:
                raise PipelineError("Cannot fetch moods from AcousticBrainz: HTTP code %d" % r.status_code)

            data = r.json()
            output = []
            for r in recordings:
                if r.mbid not in data:
                    if not self.skip_not_found:
                        output.append(r)
                    continue

                moods = {}
                for mood in ("acoustic", "aggressive", "electronic", "happy", "party", "relaxed", "sad"):
                    moods["mood_" + mood] = data[r.mbid]["0"]['highlevel']["mood_" + mood]["all"][mood]

                r.acousticbrainz["moods"] = moods
                output.append(r)
            
        return output
