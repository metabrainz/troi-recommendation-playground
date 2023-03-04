from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from time import sleep

import requests

from troi import Element, Recording


class RecentListensTimestampLookup(Element):
    """
        Element to look up the time when a user last listened given recordings in past X days.
        Note that the element is stateful and caches the recent listens lookup results!

        Timestamps are stored in the listenbrainz dict, with key name "latest_listened_at".

        :param user_name: The ListenBrainz user for whome to fetch recent listen timestamps.
        :param auth_token: a ListenBrainz auth token
        :param days: The number of days to check.
    """

    def __init__(self, user_name, days: int, auth_token=None):
        super().__init__()
        self.user_name = user_name
        self.days = days
        self.auth_token = auth_token
        self.index: Optional[dict[str, int]] = None

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def _fetch_recent_listens_index(self):
        """ Return an index of recording mbids as key and the latest listened_at time of the corresponding
        recording as values.
        """
        index = defaultdict(int)

        min_dt = datetime.now() + timedelta(days=-self.days)
        min_ts = int(min_dt.timestamp())
        while True:
            headers = {"Authorization": f"Token {self.auth_token}"} if self.auth_token else {}
            response = requests.get(
                f"https://api.listenbrainz.org/1/user/{self.user_name}/listens",
                params={"min_ts": min_ts, "count": 100},
                headers=headers
            )
            if response.status_code == 429:
                sleep(2)
                continue

            response.raise_for_status()
            data = response.json()["payload"]
            if len(data["listens"]) == 0:
                break

            for listen in data["listens"]:
                listened_at = listen["listened_at"]

                # add both user submitted mbid and mapped mbid to index

                additional_info = listen["track_metadata"]["additional_info"]
                user_submitted_mbid = additional_info.get("recording_mbid")
                if user_submitted_mbid:
                    index[user_submitted_mbid] = max(index[user_submitted_mbid], listened_at)

                mbid_mapping = listen["track_metadata"].get("mbid_mapping")
                if mbid_mapping:
                    mapped_mbid = mbid_mapping.get("recording_mbid")
                    index[mapped_mbid] = max(index[mapped_mbid], listened_at)

            min_ts = data["listens"][0]["listened_at"]

        return index

    def _get_latest_listened_ts(self, r: Recording):
        # check latest listened timestamp for original mbid
        ts1 = self.index.get(r.mbid)

        # check latest listened timstamp for canonical mbid
        ts2 = None
        if r.listenbrainz is not None and r.listenbrainz.get("canonical_recording_mbid"):
            canonical_mbid = r.listenbrainz.get("canonical_recording_mbid")
            ts2 = self.index.get(canonical_mbid)

        # if we have timestamp for both canonical and normal mbid take the maximum of two else whichever
        # one is available. if none is available continue ahead
        if ts1 and ts2:
            return max(ts1, ts2)
        elif ts1:
            return ts1
        elif ts2:
            return ts2
        else:
            return None

    def read(self, inputs):
        recordings = inputs[0]
        if not recordings:
            return []

        if self.index is None:
            self.index = self._fetch_recent_listens_index()

        for r in recordings:
            ts = self._get_latest_listened_ts(r)
            if ts is None:
                continue

            latest_listened_at = datetime.fromtimestamp(ts).replace(tzinfo=None)
            r.listenbrainz["latest_listened_at"] = latest_listened_at

        return recordings
