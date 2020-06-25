from enum import Enum

import requests
import ujson

class ListenBrainzEntityEnum(Enum):
    artist = "artist"
    release = "release"
    recording = "recording"

class ListenBrainzStatsRangeEnum(Enum):
    all_time = "all_time"
    week = "week"
    month = "month"
    year = "year"

class ListenBrainzStatsDataSource():
    '''
        Acts as common base class for fetching ListenBrainz stats.
    '''

    SERVER_URL = "https://api.listenbrainz.org/1/stats/user"

    def __init__(self, user_name, etype, range, count=None):

        if not user_name:
            raise ValueError("A valid MusicBrainz user name must be given")
        self.user_name = user_name

        if etype and isinstance(etype, ListenBrainzEntityEnum):
            self.type = etype
        else:
            try:
                self.type = ListenBrainzEntityEnum(etype)
            except ValueError:
                raise ValueError("%s is not a valid ListenBrainzEntityEnum" % str(etype))

        if range and isinstance(range, ListenBrainzStatsRangeEnum):
            self.range = range
        else:
            try:
                self.range = ListenBrainzStatsRangeEnum(range)
            except ValueError:
                raise ValueError("%s is not a valid ListenBrainzStatsRangeEnum" % str(range))
          
        if count:
            try:
                self.count = int(count)
            except ValueError:
                raise ValueError("count must be a non-zero positive integer.")
        else:
            self.count = None

    def get(self):
        url = self.SERVER_URL + "/" + self.user_name + "/" + self.type.name + "s"
        if self.range or self.count:
            args = []
            if self.range:
                args.append("range=%s" % self.range.name)
            if self.count:
                args.append("count=%d" % self.count)
            url += "?" + "&".join(args)

        print(url)
        r = requests.get(url)
        if r.status_code != 200:
            r.raise_for_status()

        try:
            response = ujson.loads(r.text)
        except Exception as err:
            raise RuntimeError(str(err))

        return response['payload'][self.type.name + "s"]
