import troi
from random import randint, shuffle
from uuid import UUID

import troi
import liblistenbrainz
import liblistenbrainz.errors
from troi import Artist, ArtistCredit, Recording
from troi import TARGET_NUMBER_OF_RECORDINGS
from troi.parse_prompt import TIME_RANGES


class LBRadioStatsRecordingElement(troi.Element):
    """
        Given a LB user, fetch their recording stats and then include recordings from it.
    """

    NUM_RECORDINGS_TO_COLLECT = TARGET_NUMBER_OF_RECORDINGS * 2

    def __init__(self, user_name, time_range, mode="easy"):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.time_range = time_range
        self.mode = mode
        self.client = liblistenbrainz.ListenBrainz()

        if time_range not in TIME_RANGES:
            raise RuntimeError("entity stats must specify one of the following time range options: " + ", ".join(TIME_RANGES))

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        if self.mode == "easy":
            offset = 0
        elif self.mode == "medium":
            offset = 100
        else:
            offset = 200

        # Fetch the user stats
        try:
            result = self.client.get_user_recordings(self.user_name, 100, offset, self.time_range)
        except liblistenbrainz.errors.ListenBrainzAPIException as err:
            raise RuntimeError("Cannot fetch recording stats for user %s" % self.user_name)

        if result is None or "recordings" not in result["payload"]:
            raise RuntimeError("There are no stats available for user '%s' for the %s time_range." %
                               (self.user_name, self.time_range))

        # Give feedback on what we collected
        self.local_storage["data_cache"]["element-descriptions"].append(f"{self.user_name}'s stats for {self.time_range}")

        # Turn them into recordings
        recordings = []
        for r in result['payload']['recordings']:
            if r['recording_mbid'] is not None:
                artists = [Artist(mbid=mbid) for mbid in r["artist_mbids"]]
                artist_credit = ArtistCredit(artists=artists, musicbrainz={"artist_mbids": r["artist_mbids"]})
                recordings.append(Recording(mbid=r['recording_mbid'], artist_credit=artist_credit))

        # Shuffle the recordings
        shuffle(recordings)

        # Check to make sure we're not going to have tracks by the same artist sequentially
        for i in range(len(recordings), 0, -1):
            try:
                if recordings[i].artist_credit.musicbrainz["artist_mbids"] == recordings[
                        i + 1].artist_credit.musicbrainz["artist_mbids"]:
                    recordings.pop(i)
            except IndexError:
                pass

        return recordings
