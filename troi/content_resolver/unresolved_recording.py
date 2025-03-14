import datetime
import logging
from collections import defaultdict
from operator import itemgetter
from time import sleep

import requests

from troi.content_resolver.model.database import db

logger = logging.getLogger(__name__)


class UnresolvedRecordingTracker:
    '''
        This class keeps track of recordings that were not resolved when
        a playlist was resolved. This will allow us to give recommendations
        on which albums to add to their collection to resolve more recordings.
    '''

    LOOKUP_BATCH_SIZE = 50

    def __init__(self):
        pass

    @staticmethod
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def multisort(xs, specs):
        """ Multiple key sort helper """
        for key, reverse in reversed(specs):
            xs.sort(key=itemgetter(key), reverse=reverse)
        return xs

    def add(self, recording_mbids):
        """
            Add one or more recording MBIDs to the unresolved recordings track. If this has
            previously been unresolved, increment the count for the number
            of times it has been unresolved.
        """

        recording_mbids = tuple(set(recording_mbids))

        placeholders = ",".join(("?", ) * len(recording_mbids))
        existing = {
                row[0]:True for row in db.execute_sql(
                """SELECT recording_mbid
                     FROM unresolved_recording
                    WHERE recording_mbid IN (%s)""" %
                placeholders, recording_mbids).fetchall()
        }

        now = datetime.datetime.now()
        with db.atomic():
            for mbid in recording_mbids:
                if mbid in existing:
                    db.execute_sql("""UPDATE unresolved_recording
                                         SET lookup_count = lookup_count + 1,
                                             last_updated = ?
                                       WHERE recording_mbid = ?""", (now, mbid))
                else:
                    db.execute_sql("""INSERT INTO unresolved_recording (recording_mbid, last_updated, lookup_count)
                                           VALUES (?, ?, ?)""", (mbid, datetime.datetime.now(), 1))


        # For when UPSERT is available on RPi
        #query = """INSERT INTO unresolved_recording (recording_mbid, last_updated, lookup_count)
        #                VALUES (?, ?, 1)
        # ON CONFLICT DO UPDATE SET lookup_count = EXCLUDED.lookup_count + 1"""

    def get_releases(self):
        """
            Organize the unresolved recordings into releases with a list of recordings.
            Return up to num_item releases.
        """

        # First call cleanup, which removes recordings that may have been recently
        # added
        self.cleanup()

        query = f"""SELECT recording_mbid
                         , lookup_count
                      FROM unresolved_recording"""

        cursor = db.execute_sql(query)
        recording_mbids = []
        lookup_counts = {}
        for row in cursor.fetchall():
            recording_mbids.append(row[0])
            lookup_counts[row[0]] = row[1]

        recording_data = {}
        for chunk in self.chunks(recording_mbids, self.LOOKUP_BATCH_SIZE):
            args = ",".join(chunk)

            params = {"recording_mbids": args, "inc": "artist release"}
            while True:
                r = requests.get("https://api.listenbrainz.org/1/metadata/recording", params=params)
                if r.status_code == 429:
                    sleep(1)
                    continue

                if r.status_code != 200:
                    logger.info("Failed to fetch metadata for recordings: ", r.text)
                    return []

                break
            recording_data.update(dict(r.json()))

        releases = defaultdict(list)
        for mbid in recording_mbids:
            try:
                rec = recording_data[mbid]
            except KeyError:
                print("Recording %s not found. Skipping." % mbid)
                continue

            releases[rec["release"]["mbid"]].append({
                "artist_name": rec["artist"]["name"],
                "artists": rec["artist"]["artists"],
                "release_name": rec["release"]["name"],
                "release_mbid": rec["release"]["mbid"],
                "release_group_mbid": rec["release"]["release_group_mbid"],
                "recording_name": rec["recording"]["name"],
                "recording_mbid": mbid,
                "lookup_count": lookup_counts[mbid]
            })

        release_list = []
        for mbid in releases:
            release = releases[mbid]
            total_count = sum([rec["lookup_count"] for rec in release])
            release_list.append({
                "mbid": release[0]["release_mbid"],
                "release_name": release[0]["release_name"],
                "artist_name": release[0]["artist_name"],
                "lookup_count": total_count,
                "recordings": release
            })

        return self.multisort(release_list, (("lookup_count", True), ("artist_name", False), ("release_name", False)))

    def print_releases(self, releases):
        """ Neatly print all the release/recordings returned from the get_releases function """

        logger.info("%-60s %-50s" % ("RELEASE", "ARTIST"))
        for release in releases:
            logger.info("%-60s %-50s" % (release["release_name"][:59], release["artist_name"][:49]))
            for rec in release["recordings"]:
                logger.info("   %-57s %d lookups" % (rec["recording_name"][:56], rec["lookup_count"]))
            logger.info("")

    def cleanup(self):
        """
            Check the local collection and remove any recordings from unresolved recordings that have
            been added to the DB.
        """

        query = f"""DELETE FROM unresolved_recording
                          WHERE recording_mbid in (
                                 SELECT recording.recording_mbid
                                   FROM recording
                                   JOIN unresolved_recording
                                     ON recording.recording_mbid = unresolved_recording.recording_mbid
                                 )"""

        cursor = db.execute_sql(query)
