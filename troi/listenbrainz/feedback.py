from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from time import sleep

import requests

from troi import Element, Recording


class ListensFeedbackLookup(Element):
    """ Element to look up the user's feedback for the given Recordings.

        :param user_name: The ListenBrainz user_name for whom to fetch feedback information.
    """

    def __init__(self, user_name, auth_token=None):
        super().__init__()
        self.user_name = user_name
        self.auth_token = auth_token

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        recordings = inputs[0]
        if not recordings:
            return []

        mbids = set()
        for r in recordings:
            mbids.add(r.mbid)
        mbids = list(mbids)

        headers = {"Authorization": f"Token {self.auth_token}"} if self.auth_token else {}

        feedback_map = {}
        batch_size = 50
        for idx in range(0, len(mbids), batch_size):
            recording_mbids = mbids[idx: idx + batch_size]

            while True:
                response = requests.get(
                    f"https://api.listenbrainz.org/1/feedback/user/{self.user_name}/get-feedback-for-recordings",
                    params={"recording_mbids": ",".join(recording_mbids)},
                    headers=headers
                )
                if response.status_code == 429:
                    sleep(2)
                    continue

                break
            response.raise_for_status()
            data = response.json()["feedback"]
            if len(data) == 0:
                continue

            for feedback in data:
                mbid = feedback["recording_mbid"]
                feedback_map[mbid] = feedback["score"]

        for r in recordings:
            r.listenbrainz["score"] = feedback_map.get(r.mbid, 0)

        return recordings
