import logging
import os
import json
import hashlib
import mutagen

from troi.content_resolver.model.database import db

logger = logging.getLogger(__name__)


class FindDuplicates:
    '''
       Class to fetch recordings that are duplicate in the database.
    '''

    def __init__(self, db):
        self.db = db

    def get_duplicate_recordings(self, include_different_releases):
        """
           Return a list of (recording_name
        """

        if include_different_releases:
            query = """SELECT recording_name
                            , release_name
                            , artist_name
                            , recording_mbid
                            , json_group_array(file_id) AS file_id
                            , COUNT(*) AS cnt
                         FROM recording
                     GROUP BY recording_mbid
                            , release_mbid
                       HAVING cnt > 1
                     ORDER BY cnt DESC, artist_name, recording_name"""
        else:
            query = """SELECT recording_name
                            , release_name
                            , artist_name
                            , recording_mbid
                            , json_group_array(file_id) AS file_id
                            , COUNT(*) AS cnt
                         FROM recording
                     GROUP BY recording_mbid
                       HAVING cnt > 1
                     ORDER BY cnt DESC, artist_name, recording_name"""

        for r in db.execute_sql(query).fetchall():
            yield (r[0], r[1], r[2], r[3], json.loads(r[4]), r[5])

    @staticmethod
    def sha1sum(filename):
        h = hashlib.sha1()
        mv = memoryview(bytearray(128*1024))
        with open(filename, 'rb', buffering=0) as f:
            while n := f.readinto(mv):
                h.update(mv[:n])
        return h.hexdigest()

    def print_duplicate_recordings(self, include_different_releases=True, verbose=False):

        total = 0
        recordings_count = 0

        def indent(n, s=''):
            return ' ' * (4 * n) + str(s)

        def print_error(e):
            logger.info(indent(2, "error: %s" % e))

        def print_info(title, content):
            logger.info(indent(2, "%s: %s" % (title, content)))

        for dup in self.get_duplicate_recordings(include_different_releases):
            recordings_count += 1
            logger.info("%d duplicates of '%s' by '%s'" % (dup[5], dup[0], dup[2]))
            for file_id in dup[4]:
                logger.info(indent(1, file_id))
                if verbose:
                    error = False
                    try:
                        file_stats = os.stat(file_id)
                        print_info("size", "%d bytes" % file_stats.st_size)
                    except Exception as e:
                        print_error(e)
                        error = True

                    if not error:
                        try:
                            print_info("sha1", self.sha1sum(file_id))
                        except Exception as e:
                            print_error(e)
                            error = True

                    if not error:
                        try:
                            mf = mutagen.File(file_id)
                            print_info("format", mf.info.pprint())
                        except mutagen.MutagenError as e:
                            print_error(e)

                total += 1
            logger.info("")

        logger.info("")
        logger.info("%d recordings had a total of %d duplicates." % (recordings_count, total))
