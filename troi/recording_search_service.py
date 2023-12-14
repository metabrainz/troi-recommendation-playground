from abc import abstractmethod

import requests

from troi.service import Service
from troi.splitter import plist


class RecordingSearchByTagService(Service):

    SLUG = "recording-search-by-tag"

    def __init__(self):
        super().__init__(self.SLUG)

    def search(self, tags, operator, begin_percent, end_percent, num_recordings):
        """
            Fetch the tag data from the LB API and return it as a dict.
        """

        data = {
            "condition": operator,
            "count": num_recordings,
            "begin_percent": begin_percent,
            "end_percent": end_percent,
            "tag": tags,
            "min_tag_count": 1
        }
        r = requests.get("https://api.listenbrainz.org/1/lb-radio/tags", params=data)
        if r.status_code != 200:
            raise RuntimeError(f"Cannot fetch recordings for tags. {r.text}")

        return self.flatten_tag_data(dict(r.json()))

    def flatten_tag_data(self, tag_data):

        flat_data = list(tag_data["recording"])
        flat_data.extend(list(tag_data["release-group"]))
        flat_data.extend(list(tag_data["artist"]))

        return plist(sorted(flat_data, key=lambda f: f["percent"], reverse=True))
