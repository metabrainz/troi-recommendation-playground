import troi
from random import randint, shuffle
from uuid import UUID

import troi
import liblistenbrainz
import liblistenbrainz.errors
from troi import Artist, Recording
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.parse_prompt import TIME_RANGES


class LBRadioRecommendationRecordingElement(troi.Element):
    """
        Given a LB user, fetch their recommended recordings and then include recordings from it.
    """

    MAX_RECOMMENDED_RECORDINGS = 1000
    MAX_RECORDINGS_TO_FETCH_PER_CALL = 100

    def __init__(self, user_name, listened="all", mode="easy", auth_token=None):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.listened = listened
        self.mode = mode
        self.client = liblistenbrainz.ListenBrainz()
        if auth_token:
            self.client.set_auth_token(auth_token)

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def _select_recs(self, candidates, target):
        recordings = []
        for r in candidates:
            if r.get("recording_mbid") is None:
                continue
            latest = r.get("latest_listened_at")
            if self.listened == "all" or \
                    (self.listened == "unlistened" and latest is None) or \
                    (self.listened == "listened" and latest is not None):
                recordings.append(Recording(mbid=r["recording_mbid"]))
                if len(recordings) >= target:
                    break
        return recordings

    def read(self, entities):

        if self.mode == "easy":
            offset = 0
        elif self.mode == "medium":
            offset = self.MAX_RECOMMENDED_RECORDINGS // 3
        else:
            offset = self.MAX_RECOMMENDED_RECORDINGS * 2 // 3

        target = self.MAX_RECOMMENDED_RECORDINGS // 3

        service = self.patch.services.get("recs") if self.patch else None
        if service is not None:
            recordings = self._select_recs((service.fetch(self.user_name) or [])[offset:], target)
        else:
            recordings = []
            count = target
            while count > 0:
                # Fetch the user recs
                try:
                    result = self.client.get_user_recommendation_recordings(self.user_name, "raw",
                                                                            min(self.MAX_RECORDINGS_TO_FETCH_PER_CALL, count), offset)
                except liblistenbrainz.errors.ListenBrainzAPIException:
                    raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

                if result is None or len(result['payload']['mbids']) == 0:
                    break

                # Turn them into recordings
                page = result['payload']['mbids']
                selected = self._select_recs(page, count)
                recordings.extend(selected)
                count -= len(selected)
                offset += sum(1 for r in page if r.get("recording_mbid") is not None)

        # Shuffle the recordings
        shuffle(recordings)

        # Give feedback on what we collected
        listened = ""
        if self.listened != "all":
            listened = f"previously {self.listened} "

        self.local_storage["data_cache"]["element-descriptions"].append(f"{self.user_name}'s {listened}recommended songs")

        # TODO: How do we prevent sequential tracks by the same artist?

        return recordings
