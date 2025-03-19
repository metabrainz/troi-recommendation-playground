import logging
from collections import defaultdict, namedtuple
import datetime
from time import sleep

import requests
from tqdm import tqdm

from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, RecordingMetadata
from troi.content_resolver.model.tag import RecordingTag

logger = logging.getLogger("troi_metadata_lookup")


RecordingRow = namedtuple('RecordingRow', ('id', 'mbid', 'metadata_id'))


class MetadataLookup:
    '''
    Given the local database, lookup metadata from MusicBrainz to allow local playlist resolution.
    '''

    BATCH_SIZE = 1000

    def __init__(self, quiet=False):
        self.quiet = quiet

    def lookup(self):
        """
        Iterate over all recordings in the database and call lookup_chunk for chunks of recordings.
        """

        cursor = db.execute_sql("""SELECT recording.id, recording.recording_mbid, recording_metadata.id
                                     FROM recording
                                LEFT JOIN recording_metadata
                                       ON recording.id = recording_metadata.recording_id
                                    WHERE recording_mbid IS NOT NULL
                                 ORDER BY artist_name, release_name""")
        recordings = tuple(
            RecordingRow(id=row[0], mbid=str(row[1]), metadata_id=row[2])
            for row in cursor.fetchall()
        )

        logger.info("[ %d recordings to lookup ]" % len(recordings))

        offset = 0

        if not self.quiet:
            with tqdm(total=len(recordings)) as self.pbar:
                while offset <= len(recordings):
                    self.process_recordings(recordings[offset:offset+self.BATCH_SIZE])
                    offset += self.BATCH_SIZE
        else:
            while offset <= len(recordings):
                self.process_recordings(recordings[offset:offset+self.BATCH_SIZE])
                offset += self.BATCH_SIZE

    def process_recordings(self, recordings):
        """
            This function carries out the actual lookup of the metadata and inserting the
            popularity and tags into the DB for the given chunk of recordings.
        """

        args = []
        mbid_to_recording = {}
        for rec in recordings:
            mbid_to_recording[rec.mbid] = rec
            args.append({"recording_mbid": rec.mbid})

        while True:
            r = requests.post("https://labs.api.listenbrainz.org/bulk-tag-lookup/json", json=args)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                logger.info("Fail: %d %s" % (r.status_code, r.text))
                return False

            break

        recording_pop = {}
        recording_tags = defaultdict(lambda: defaultdict(list))
        tags = set()
        for row in r.json():
            mbid = str(row["recording_mbid"])
            recording_pop[mbid] = row["percent"]
            recording_tags[mbid][row["source"]].append(row["tag"])
            tags.add(row["tag"])

        if not self.quiet:
            self.pbar.update(len(recordings))

        with db.atomic():

            # This DB code is pretty messy -- things I take for granted with Postgres are not
            # available in SQLite or the PeeWee ORM. But, this might be ok, since we're not
            # updating millions of rows constantly.

            # First update recording_metadata table
            for mbid in set(recording_pop):
                recording = mbid_to_recording[mbid]
                if recording.metadata_id is None:
                    recording_metadata = RecordingMetadata.create(recording=recording.id,
                                                                  popularity=recording_pop[mbid],
                                                                  last_updated=datetime.datetime.now())
                    recording_metadata.save()
                else:
                    recording_metadata = RecordingMetadata.replace(id=recording.metadata_id,
                                                                   recording=recording.id,
                                                                   popularity=recording_pop[mbid],
                                                                   last_updated=datetime.datetime.now())

                    recording_metadata.execute()

            # Next delete recording_tags
            RecordingTag.delete().where(
                RecordingTag.recording_id.in_(
                    Recording.select(Recording.id).where(
                        Recording.recording_mbid.in_(set(recording_tags))

                    )
                )
            ).execute()
            # This is the better way to insert the tags into the DB, but on some installations
            # of Sqlite/Python the UPSERT is not supported. Once it is widely supported,
            # remove the section below and uncomment this.
            #tag_ids = {}
            #for tag in tags:
            #    cursor = db.execute_sql("""INSERT INTO tag (name)
            #                                    VALUES (?)
            #                 ON CONFLICT DO UPDATE SET name = ? RETURNING id""", (tag,tag))
            #    row = cursor.fetchone()
            #    tag_ids[tag] = row[0]

            # insert new recording tags
            for tag in tags:
                db.execute_sql("""INSERT OR IGNORE INTO tag (name) VALUES (?)""", (tag,))

            tag_str = ",".join([ "'%s'" % t.replace("'", "''") for t in tags])
            cursor = db.execute_sql("""SELECT id, name FROM tag WHERE name IN (%s)""" % tag_str)
            tag_ids = {row[1]: row[0] for row in cursor.fetchall()}

            # insert recording_tag rows
            with db.atomic():
                now = datetime.datetime.now()
                for row in r.json():
                    recording = mbid_to_recording[row["recording_mbid"]]
                    db.execute_sql("""INSERT INTO recording_tag (recording_id, tag_id, entity, last_updated)
                                       VALUES (?, ?, ?, ?)""", (recording.id, tag_ids[row["tag"]], row["source"], now))

        return True
