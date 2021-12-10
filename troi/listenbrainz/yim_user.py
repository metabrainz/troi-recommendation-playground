import psycopg2
from psycopg2.errors import OperationalError
import psycopg2.extras

from troi import Element, User

LB_CONNECT_URI = "postgresql://listenbrainz:listenbrainz@localhost:65400/listenbrainz"


class YIMUserListElement(Element):
    '''
        This element is used to fetch a list of users who need to have playlists generated for them.
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [User]

    def read(self, inputs):

        with psycopg2.connect(LB_CONNECT_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:

                query = """SELECT "user".musicbrainz_id AS user_name
                             FROM "user"
                             JOIN statistics.year_in_music yim
                               ON "user".id = yim.user_id
                            WHERE yim.data->'playlists'->>'slug' is NULL
                            LIMIT 100"""
                curs.execute(query)

                return [ User(user_name=row["user_name"]) for row in curs.fetchall()]
