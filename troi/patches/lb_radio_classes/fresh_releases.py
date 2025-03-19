from datetime import date, timedelta
from random import shuffle
import requests
from time import sleep

import troi
from troi.plist import plist
from troi import Artist, ArtistCredit, Recording
from troi import TARGET_NUMBER_OF_RECORDINGS


class LBRadioFreshReleasesRecordingElement(troi.Element):
    """
        Given a LB user, fetch their fresh releases and make a playlist from it
    """

    SERVER_URL = "https://api.listenbrainz.org/1/user/%s/fresh_releases?future=false"

    def __init__(self, user_name, mode, range="week"):
        troi.Element.__init__(self)
        self.user_name = user_name
        self.mode = mode
        self.range = range
        if self.range not in ("week", "month"):
            raise troi.PipelineError("option range must be either 'week' or 'month'")
        print(range)

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def load_recordings(self, release_data, days):

        headers = {"User-Agent": f"Troi (rob@meb!)"}

        today = date.today()
        recordings = [] 
        for release in release_data:
            while True:
                r = requests.get("https://musicbrainz.org/ws/2/release/%s?inc=recordings&fmt=json" % release["release_mbid"], headers=headers)
                if r.status_code == 503:
                    sleep(2)
                    continue

                if r.status_code != 200:
                    raise troi.PipelineError("Cannot fetch recordings from MusicBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

                break

            from icecream import ic
            data = r.json()
            for media in data["media"]:
                for track in media["tracks"]:
                    first_date = track["recording"]["first-release-date"]
                    if len(first_date) == 4:
                        first_date += "-01-01"
                    elif len(first_date) == 7:
                        first_date += "-01"
                    dt = date.fromisoformat(first_date)
                    delta = today - dt
                    if abs(delta.days) <= days: 
                        print("accept %-30s %s" % (track["title"][:30], first_date))
                        recordings.append(Recording(name=track["title"], mbid=track["recording"]["id"] ))

        shuffle(recordings)
        return plist(recordings)

    def read(self, inputs):

        while True:
            r = requests.get(self.SERVER_URL % self.user_name)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise troi.PipelineError("Cannot fetch fresh releases from ListenBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

            break

        data = r.json()["payload"]
        releases_to_use = []
        
        today = date.today()
        days = 8 if self.range == "week" else 32  # see what I did here? #timezonesarehard
        for rel in data["releases"]:
            dt = date.fromisoformat(rel["release_date"])
            delta = today - dt
            if abs(delta.days) <= days: 
                releases_to_use.append(rel)
                
        self.local_storage["data_cache"]["element-descriptions"].append(f"Fresh Releases for {self.user_name} in the past {self.range}")
        return self.load_recordings(releases_to_use, days) 
