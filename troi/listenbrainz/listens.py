from collections import defaultdict
from datetime import datetime, timedelta

import requests

from troi import Element, Recording


class RecentListensTimestampLookup(Element):
    """ Element to look up the time when a user last listened given recordings in past X days. Note that the
    element is stateful and caches the recent listens lookup results.
    """

    def __init__(self, user_name, days: int):
        super().__init__()
        self.user_name = user_name
        self.days = days
        self.index = None

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def get_recording_mbid(listen):
        """ Retrieve recording_mbid of the listen, prefer user submitted mbid to mbid mapping one """
        additional_info = listen["track_metadata"]["additional_info"]
        mbid = additional_info.get("recording_mbid")

        if mbid:
            return mbid

        mbid_mapping = listen["track_metadata"].get("mbid_mapping")
        if mbid_mapping:
            return mbid_mapping.get("recording_mbid")

    def _fetch_recent_listens_index(self):
        """ Return an index of recording mbids as key and the latest listened_at time of the corresponding
        recording as values.
        """
        index = defaultdict(int)

        min_dt = datetime.now() + timedelta(days=-self.days)
        min_ts = int(min_dt.timestamp())
        while True:
            response = requests.get(
                f"https://api.listenbrainz.org/1/user/{self.user_name}/listens",
                params={"min_ts": min_ts, "count": 100}
            )
            response.raise_for_status()
            data = response.json()["payload"]
            if len(data["listens"]) == 0:
                break

            for listen in data["listens"]:
                listened_at = listen["listened_at"]
                mbid = self.get_recording_mbid(listen)

                if mbid:
                    index[mbid] = max(index[mbid], listened_at)

            min_ts = data["listens"][0]["listened_at"]

        return index

    def read(self, inputs):
        recordings = inputs[0]
        if not recordings:
            return []

        if self.index is None:
            self.index = self._fetch_recent_listens_index()

        for r in recordings:
            if r.mbid not in self.index:
                continue

            ts = self.index[r.mbid]
            latest_listened_at = datetime.fromtimestamp(ts).replace(tzinfo=None)

            if r.listenbrainz is not None:
                r.listenbrainz["latest_listened_at"] = latest_listened_at
            else:
                r.listenbrainz = {"latest_listened_at": latest_listened_at}

        return recordings
