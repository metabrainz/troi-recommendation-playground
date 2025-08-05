import logging
from collections import defaultdict, namedtuple
import datetime
import json
from time import sleep

from tqdm import tqdm
from peewee import fn

from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, RecordingMetadata, Artist, ArtistCredit, RecordingArtistCredit
from troi.content_resolver.model.tag import RecordingTag
from troi.http_request import http_post

logger = logging.getLogger("troi_subsonic_scan")
APP_LOG_LEVEL_NUM = 19
logging.addLevelName(APP_LOG_LEVEL_NUM, "NOTICE")

RecordingRow = namedtuple('RecordingRow', ('id', 'mbid', 'metadata_id'))

class MetadataLookup:
    '''
    Given the local database, lookup metadata from MusicBrainz to allow local playlist resolution.
    '''

    BATCH_SIZE = 1000

    def __init__(self, quiet=False):
        self.quiet = quiet

    def lookup(self, server_slug):
        """
        Iterate over all recordings in the database and call lookup_chunk for chunks of recordings.
        """

        cursor = db.execute_sql("""SELECT recording.id, recording.recording_mbid, recording_metadata.id
                                     FROM recording
                                LEFT JOIN recording_metadata
                                       ON recording.id = recording_metadata.recording_id
                                    WHERE recording_mbid IS NOT NULL
                                      AND recording.file_source = ?
                                 ORDER BY artist_name, release_name""", (server_slug,))
        recordings = tuple(
            RecordingRow(id=row[0], mbid=str(row[1]), metadata_id=row[2])
            for row in cursor.fetchall()
        )

        logger.info("looking up metadata for %d recordings" % len(recordings))

        offset = 0
        self.count = 0
        total_recordings = len(recordings) * 2  # We have metadata and tags to look up
        if not self.quiet:
            with tqdm(total=total_recordings) as self.pbar:
                while offset <= len(recordings):
                    self.lookup_tags(recordings[offset:offset+self.BATCH_SIZE])
                    self.lookup_metadata(recordings[offset:offset+self.BATCH_SIZE])
                    offset += self.BATCH_SIZE
                    print(self.count)
                    percent = 100 * self.count // total_recordings
                    logger.log(logging.INFO, "%d recordings looked up." % self.count)
                    logger.log(APP_LOG_LEVEL_NUM, "json-" + json.dumps((("Current task", "ListenBrainz metadata lookup"),
                                                                      ("Recordings looked up", f"{self.count:,} ({percent}%)"),
                                                                      ("Total recordings", f"{total_recordings:,}"),
                                                                      ("Progress", percent))))
        else:
            while offset <= len(recordings):
                self.process_recordings(recordings[offset:offset+self.BATCH_SIZE])
                offset += self.BATCH_SIZE

        logger.info("[ metadata lookup complete ]")

    def lookup_tags(self, recordings):
        """
            This function carries out the fetching of the tags by
            popularity and inserts them into the DB for the given chunk of recordings.
        """
        
        args = []
        mbid_to_recording = {}
        for rec in recordings:
            mbid_to_recording[rec.mbid] = rec
            args.append({"recording_mbid": rec.mbid})

        r = http_post("https://labs.api.listenbrainz.org/bulk-tag-lookup/json", json=args)
        if r.status_code != 200:
            logger.info("Fail: %d %s" % (r.status_code, r.text))
            return 0

        recording_pop = {}
        recording_tags = defaultdict(lambda: defaultdict(list))
        tag_counts = {}
        tags = set()
        for row in r.json():
            mbid = str(row["recording_mbid"])
            recording_pop[mbid] = row["percent"]
            recording_tags[mbid][row["source"]].append(row["tag"])
            tags.add(row["tag"])
            tag_counts[row["recording_mbid"] + row["tag"]] = str(row["tag_count"])


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
                    db.execute_sql("""INSERT INTO recording_tag (recording_id, tag_id, count, entity, last_updated)
                                       VALUES (?, ?, ?, ?, ?)""", (recording.id,
                                                                tag_ids[row["tag"]],
                                                                tag_counts[row["recording_mbid"] + row["tag"]],
                                                                row["source"], now))
        self.count += len(recordings)
        if not self.quiet:
            self.pbar.update(len(recordings))


    def lookup_metadata(self, recordings):
        """
            This function carries out the lookup of the artist/year metadata and
            inserts it into the DB for the given chunk of recordings.
        """

        mbid_to_recording = {}
        mbids = []
        for rec in recordings:
            mbid_to_recording[rec.mbid] = rec
            mbids.append(rec.mbid)
            
        args = {
            "recording_mbids": mbids,
            "inc": "artist release"
        }
        r = http_post("https://api.listenbrainz.org/1/metadata/recording", json=args)
        if r.status_code != 200:
            logger.info("Fail: %d %s" % (r.status_code, r.text))
            return 0

        # This will collect all the data we want to upsert into the db
        data = r.json()
        artist_credits = {}
        artists = {}
        recording_artist_credits = []
        recording_year_mapping = []
        for recording_mbid in data.keys():
            artist_credit = data[recording_mbid]["artist"]
            for artist in artist_credit["artists"]:
                mbid = artist["artist_mbid"]
                ar_data = { "artist_credit": artist_credit["artist_credit_id"],
                            "mbid": mbid,
                            "name": artist["name"],
                            "join_phrase": artist["join_phrase"] }
                if "area" in artist and artist["area"]:
                    ar_data["area"] = artist["area"]
                if "gender" in artist and artist["gender"]:
                    ar_data["gender"] = artist["gender"]
                if "type" in artist and artist["type"]:
                    ar_data["type"] = artist["type"]
                    
                artists[mbid] = ar_data
                
            release = data[recording_mbid]["release"]
            if "year" in release and release["year"]:
                recording_year_mapping.append((recording_mbid, release["year"]))
                
            if artist_credit["artist_credit_id"] not in artist_credits:
                ac = { "id": artist_credit["artist_credit_id"],
                       "name": artist_credit["name"] }
                artist_credits[artist_credit["artist_credit_id"]] = ac
                
            recording_artist_credits.append({ "recording": mbid_to_recording[recording_mbid].id,
                                              "artist_credit": artist_credit["artist_credit_id"]
                                            })
            
        with db.atomic():
            query = ArtistCredit.insert_many(artist_credits.values()).on_conflict(
                conflict_target=(ArtistCredit.id),
                preserve=[ArtistCredit.name],
                update={'name': fn.EXCLUDED}
            )
            query.execute()

            query = Artist.insert_many(artists.values()).on_conflict(
                conflict_target=[Artist.mbid],
                preserve=[Artist.name, Artist.join_phrase, Artist.area, Artist.gender, Artist.type],
                update={'name': fn.EXCLUDED, 'join_phrase': fn.EXCLUDED, 'area': fn.EXCLUDED, 'gender': fn.EXCLUDED, 'type': fn.EXCLUDED}
            )
            query.execute() 

            query = RecordingArtistCredit.insert_many(recording_artist_credits).on_conflict(
                conflict_target=(RecordingArtistCredit.recording),
                action='NOTHING'
            )
            query.execute()
            
            args = []
            query = """UPDATE recording SET year = CASE """
            for mbid, year in recording_year_mapping:
                query += "WHEN recording_mbid = ? THEN ? "
                args.extend([mbid, year])
            query += "END"
            db.execute_sql(query, args) 

        self.count += len(recordings)
        if not self.quiet:
            self.pbar.update(len(recordings))
