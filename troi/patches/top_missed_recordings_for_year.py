from datetime import datetime

import psycopg2
import psycopg2.extras

import troi
from troi import Recording, Element
from troi.playlist import PlaylistMakerElement
from troi.musicbrainz.recording_lookup import RecordingLookupElement



class MissedRecordingsElement(Element):

    """ This element looks up top tracks for 3 users minus the tracks of one given user to form 
        the core of the missed tracks playlist for yim. """

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
                             FROM mapping.tracks_of_the_year_2022 t
                            WHERE user_id = %s
                         ) SELECT recording_mbid::TEXT
                                , sum(listen_count) AS listen_count
                             FROM mapping.tracks_of_the_year_2022 t
                            WHERE user_id IN %s
                              AND recording_mbid NOT IN (SELECT * FROM exclude_tracks)
                         GROUP BY recording_mbid
                         ORDER BY listen_count DESC
                            LIMIT 200"""
 
                curs.execute(query, (self.user_id, tuple(self.similar_user_ids)))
                output = []
                while True:
                    row = curs.fetchone()
                    if not row:
                        break

                    output.append(Recording(mbid=row["recording_mbid"], listenbrainz={"listen_count": row["listen_count"]}))

                return output


class TopMissedTracksPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Top Missed Recordings of %d for %s"
    DESC = """<p>
                This playlist features recordings that were listened to by users similar to %s in %d.
                It is a discovery playlist that aims to introduce you to new music that other similar users
                enjoy. It may require more active listening and may contain tracks that are not to your taste.
              </p>
              <p>
                The users similar to you who contributed to this playlist: %s.
              </p>
              <p>
                For more information on how this playlist is generated, please see our
                <a href="https://musicbrainz.org/doc/YIM2022Playlists">Year in Music 2022 Playlists</a> page.
              </p>
           """

    def __init__(self, args, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, args, debug)
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
        user_id = int(inputs['user_id'])
        user_name = inputs['user_name'] 
        lb_db_connect_str = inputs['lb_db_connect_str'] 
        mb_db_connect_str = inputs['mb_db_connect_str'] 

        similar_users = None
        with psycopg2.connect(mb_db_connect_str) as mb_conn,\
            mb_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as mb_curs:
                mb_curs.execute("SELECT similar_users FROM recommendation.similar_user WHERE user_id = %s", (user_id,))
                similar_users = mb_curs.fetchone()

                if similar_users is None:
                    return []

                similar_user_ids = []
                similar_users = [ (i, similar_users[0][i][0]) for i in similar_users[0] ]
                for user in sorted(similar_users, key=lambda item: item[1], reverse=True)[:3]:
                    similar_user_ids.append(int(user[0]))

                mb_curs.execute("""SELECT id, musicbrainz_id FROM "user" WHERE id IN %s""", (tuple(similar_user_ids),))
                your_peeps = ", ".join([ f'<a href="https://listenbrainz.org/user/{r["musicbrainz_id"]}/">{r["musicbrainz_id"]}</a>'
                                          for r in mb_curs.fetchall() ])
                print(your_peeps)


        missed = MissedRecordingsElement(user_id, similar_user_ids, lb_db_connect_str)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(missed)

        year = datetime.now().year
        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year, user_name),
                                                      self.DESC % (user_name, year, your_peeps),
                                                      patch_slug=self.slug(),
                                                      user_name=user_name,
                                                      max_artist_occurrence=2)
        pl_maker.set_sources(rec_lookup)

        return pl_maker
