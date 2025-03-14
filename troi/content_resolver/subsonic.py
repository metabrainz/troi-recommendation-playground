import datetime
import logging

from libsonic.errors import DataNotFoundError
import peewee
from tqdm import tqdm

from troi.content_resolver.database import Database
from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, FileIdType
from troi.content_resolver.utils import bcolors
from troi.content_resolver.py_sonic_fix import FixedConnection

logger = logging.getLogger(__name__)


class SubsonicDatabase(Database):
    '''
    Add subsonic sync capabilities to the Database
    '''

    # Determined by the number of albums we can fetch in one go
    BATCH_SIZE = 500

    def __init__(self, index_dir, config, quiet=False):
        self.config = config
        Database.__init__(self, index_dir, quiet)
        self.quiet = quiet

    def sync(self):
        """
            Scan the subsonic client specified in config.py
        """

        # Keep some stats
        self.total = 0
        self.matched = 0
        self.error = 0

        self.run_sync()

        logger.info("Checked %s albums:" % self.total)
        logger.info("  %5d albums matched" % self.matched)
        logger.info("  %5d recordings with errors" % self.error)

    def connect(self):
        if not self.config:
            logger.error("Missing credentials to connect to subsonic")
            return None

        logger.info("[ connect to subsonic ]")

        return FixedConnection(
            self.config.SUBSONIC_HOST,
            username=self.config.SUBSONIC_USER,
            port=self.config.SUBSONIC_PORT,
            salt=self.config.SUBSONIC_SALT,
            token=self.config.SUBSONIC_TOKEN,
        )

    def run_sync(self):
        """
            Perform the sync between the local collection and the subsonic one.
        """

        conn = self.connect()
        if not conn:
            return

        cursor = db.connection().cursor()

        logger.info("[ load albums ]")
        album_ids = set()
        albums = []
        offset = 0
        while True:
            results = conn.getAlbumList2(ltype="alphabeticalByArtist", size=self.BATCH_SIZE, offset=offset)
            albums.extend(results["albumList2"]["album"])
            album_ids.update([r["id"] for r in results["albumList2"]["album"]])

            album_count = len(results["albumList2"]["album"])
            offset += album_count
            if album_count < self.BATCH_SIZE:
                break

        logger.info("[ loaded %d albums ]" % len(album_ids))

        if not self.quiet:
            pbar = tqdm(total=len(album_ids))
        recordings = []

        # cross reference subsonic artist id to artitst_mbid
        artist_id_index = {}

        for album in albums:
            album_info = conn.getAlbum(id=album["id"])

            # Some servers might already include the MBID in the list or album response
            album_mbid = album_info.get("musicBrainzId", album.get("musicBrainzId"))
            if not album_mbid:
                album_info2 = conn.getAlbumInfo2(aid=album["id"])
                try:
                    album_mbid = album_info2["albumInfo"]["musicBrainzId"]
                except KeyError:
                    if not self.quiet:
                        pbar.write(bcolors.FAIL + "FAIL " + bcolors.ENDC + "subsonic album '%s' by '%s' has no MBID" %
                                   (album["name"], album["artist"]))
                    self.error += 1
                    continue


            recordings = []
            for song in album_info["album"]["song"]:
                album = album_info["album"]

                if "artistId" in song:
                    artist_id = song["artistId"]
                else:
                    artist_id = album["artistId"]

                if artist_id not in artist_id_index:
                    artist = conn.getArtistInfo2(artist_id)
                    try:
                        artist_id_index[artist_id] = artist["artistInfo2"]["musicBrainzId"]
                    except KeyError:
                        if not self.quiet:
                            pbar.write(bcolors.FAIL + "FAIL " + bcolors.ENDC + "recording '%s' by '%s' has no artist MBID" %
                                    (album["name"], album["artist"]))
                            pbar.write("Consider retagging this file with Picard! ( https://picard.musicbrainz.org )")
                        self.error += 1
                        continue

                self.add_subsonic({
                    "artist_name": song["artist"],
                    "release_name": song["album"],
                    "recording_name": song["title"],
                    "artist_mbid": artist_id_index[artist_id],
                    "release_mbid": album_mbid,
                    "recording_mbid": song["musicBrainzId"],
                    "duration": song["duration"] * 1000,
                    # Neither track number nor disc number are guaranteed for subsonic
                    "track_num": song.get("track", 1),
                    "disc_num": song.get("discNumber", 1),
                    "subsonic_id": song["id"],
                    "mtime": datetime.datetime.now()
                    })

            if not self.quiet:
                pbar.write(bcolors.OKGREEN + "OK   " + bcolors.ENDC + "album %-50s %-50s" %
                           (album["name"][:49], album["artist"][:49]))
            self.matched += 1
            self.total += 1
            if not self.quiet:
                pbar.update(1)

        if len(recordings) >= self.BATCH_SIZE:
            self.update_recordings(recordings)

    def add_subsonic(self, mdata):
        """
            Given recording metadata, add it to the database or update it if it already exists
            update the recording instead
        """

        with db.atomic() as transaction:
            try:
                recording = Recording.select().where(Recording.file_id == mdata['subsonic_id']).get()
                recording.artist_name = mdata["artist_name"]
                recording.release_name = mdata["release_name"]
                recording.recording_name = mdata["recording_name"]
                recording.artist_mbid = mdata["artist_mbid"]
                recording.release_mbid = mdata["release_mbid"]
                recording.recording_mbid = mdata["recording_mbid"]
                recording.mtime = mdata["mtime"]
                recording.track_num = mdata["track_num"]
                recording.disc_num = mdata["disc_num"]
                recording.save()
                return "updated"
            except peewee.DoesNotExist:
                recording = Recording.create(file_id=mdata["subsonic_id"],
                                             file_id_type=FileIdType(FileIdType.SUBSONIC_ID),
                                             artist_name=mdata["artist_name"],
                                             release_name=mdata["release_name"],
                                             recording_name=mdata["recording_name"],
                                             artist_mbid=mdata["artist_mbid"],
                                             release_mbid=mdata["release_mbid"],
                                             recording_mbid=mdata["recording_mbid"],
                                             mtime=mdata["mtime"],
                                             duration=mdata["duration"],
                                             track_num=mdata["track_num"],
                                             disc_num=mdata["disc_num"])
                recording.save()
                return "added"


    def update_recordings(self, recordings):
        """
            Given a list of recording_subsonic records, update the DB.
            Updates recording_id, subsonic_id, last_update
        """

        recording_index = { r[0]:r[1] for r in recordings }

        cursor = db.connection().cursor()
        with db.atomic():

            placeholders = ",".join(("?", ) * len(recording_index))
            cursor.execute("""SELECT recording_id
                                FROM recording_subsonic
                               WHERE recording_id in (%s)""" % placeholders, tuple(recording_index.keys()))
            existing_ids = { row[0]:None for row in cursor.fetchall() }
            existing_recordings = []
            new_recordings = []
            for r in recordings:
                if r[0] in existing_ids:
                    existing_recordings.append((r[0], r[1], datetime.datetime.now(), r[0]))
                else:
                    new_recordings.append((r[0], r[1], datetime.datetime.now()))

            cursor.executemany("""INSERT INTO recording_subsonic (recording_id, subsonic_id, last_updated)
                                       VALUES (?, ?, ?)""", tuple(new_recordings))

            cursor.executemany("""UPDATE recording_subsonic
                                     SET recording_id = ?
                                       , subsonic_id = ?
                                       , last_updated = ?
                                   WHERE recording_id = ?""", tuple(existing_recordings))


        # This concise query does the same as above. But older versions of python/sqlite on Raspberry Pis
        # don't support upserts yet. :(
        #recordings = [(r[0], r[1], datetime.datetime.now()) for r in recordings]
        #cursor.executemany(
        #    """INSERT INTO recording_subsonic (recording_id, subsonic_id, last_updated)
        #                            VALUES (?, ?, ?)
        #         ON CONFLICT DO UPDATE SET recording_id = excluded.recording_id
        #                                 , subsonic_id = excluded.subsonic_id
        #                                 , last_updated = excluded.last_updated""", recordings)

    def upload_playlist(self, playlist, playlist_id=None):
        """
            Given a Troi playlist, upload the playlist to the subsonic API.
        """

        conn = self.connect()
        if not conn:
            return

        song_ids = []
        for recording in playlist.playlists[0].recordings:
            try:
                song_ids.append(recording.musicbrainz["subsonic_id"])
            except KeyError:
                continue

        if playlist_id:
            try:
                remote_playlist = conn.getPlaylist(pid=playlist_id)
                removed_song_idx = list(range(0, remote_playlist["playlist"]["songCount"]))
                conn.updatePlaylist(
                    lid=playlist_id,
                    name=playlist.playlists[0].name,
                    songIdsToAdd=song_ids,
                    songIndexesToRemove=removed_song_idx,
                )
            except DataNotFoundError:
                conn.createPlaylist(name=playlist.playlists[0].name, songIds=song_ids)
        else:
            conn.createPlaylist(name=playlist.playlists[0].name, songIds=song_ids)
