from datetime import datetime

import psycopg2
import psycopg2.extras

import troi
from troi import Recording, Element
from troi.playlist import PlaylistShuffleElement, PlaylistRedundancyReducerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement



class MissedRecordingsElement(Element):

    def __init__(self, user_id, similar_user_ids, db_connect_str):
        Element.__init__(self)
        self.user_id = user_id
        self.similar_user_ids = similar_user_ids
        self.db_connect_str = db_connect_str

    @staticmethod
    def inputs():
        return [ ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):

        output = []
        with psycopg2.connect(self.db_connect_str) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
 
                query = """WITH exclude_tracks AS (
                           SELECT recording_mbid
                             FROM mapping.tracks_of_the_year t
                            WHERE user_id = %s
                       ) SELECT recording_mbid
                              , recording_name
                              , sum(listen_count) AS listen_count
                             FROM mapping.tracks_of_the_year t
                            WHERE user_id IN (%s, %s, %s)
                              AND recording_mbid NOT IN (SELECT * FROM exclude_tracks)
                         GROUP BY recording_mbid, recording_name, artist_credit_name, artist_mbids
                         ORDER BY listen_count DESC
                            LIMIT 100"""
 
                users = [ self.user_id ] 
                users.extend(self.similar_user_ids)
                curs.execute(query, tuple(users))
                output = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    output.append(Recording(mbid=row["recording_mbid"]))

                return output


class TopMissedTracksPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Missed Recordings of %d for %s"
    DESC = """<p>
                There were too many words, so let keep it short: Here is your playlist."
              </p>
              <p>
                Your peeps: %s
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        """
        Generate a top missed tracks playlists for a given user.

        \b
        USER_NAME: is a MusicBrainz user name that has an account on ListenBrainz.
        """
        return [{"type": "argument", "args": ["user_id"]},
                {"type": "argument", "args": ["user_name"]},
                {"type": "argument", "args": ["lb_db_connect_str"]},
                {"type": "argument", "args": ["mb_db_connect_str"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-missed-recordings-for-year"

    @staticmethod
    def description():
        return "Generate a playlist from the top tracks that the most similar users listened to, but the user didn't listen to."

    def create(self, inputs):
        user_id = inputs['user_id'] 
        user_name = inputs['user_name'] 
        lb_db_connect_str = inputs['lb_db_connect_str'] 
        mb_db_connect_str = inputs['mb_db_connect_str'] 

        similar_users = None
        with psycopg2.connect(lb_db_connect_str) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute("""SELECT similar_users
                                  FROM recommendation.similar_user
                                 WHERE user_id = %s""", (user_id,))
                similar_users = curs.fetchone()

                if similar_users is None:
                    return []

                similar_users = [ (i, similar_users[0][i][0]) for i in similar_users[0] ]

                similar_user_ids = []
                for user in sorted(similar_users, key=lambda item: item[1], reverse=True)[:3]:
                    similar_user_ids.append(int(user[0]))

                curs.execute("""SELECT id
                                     , musicbrainz_id
                                  FROM "user"
                                 WHERE id IN %s""", (tuple(similar_user_ids),))
                your_peeps = ", ".join([ r["musicbrainz_id"] for r in curs.fetchall() ])


        missed = MissedRecordingsElement(user_id, similar_user_ids, mb_db_connect_str)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(missed)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, inputs['user_name']),
                                                      self.DESC % (your_peeps),
                                                      patch_slug=self.slug(),
                                                      user_name=inputs['user_name'])
        pl_maker.set_sources(rec_lookup)

        reducer = PlaylistRedundancyReducerElement(max_num_recordings=self.max_num_recordings)
        reducer.set_sources(pl_maker)

        return reducer
