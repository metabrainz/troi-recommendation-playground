import psycopg2
from psycopg2.errors import OperationalError
import psycopg2.extras

from troi import Element, User

MB_CONNECT_URI = "postgresql://musicbrainz:musicbrainz@localhost:25432/musicbrainz_db"


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

        with psycopg2.connect(MB_CONNECT_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:

                query = """SELECT DISTINCT user_name
                             FROM mapping.tracks_of_the_year
                         ORDER BY user_name"""

                curs.execute(query)

                return [ User(user_name=row["user_name"]) for row in curs.fetchall()]
