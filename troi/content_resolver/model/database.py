from peewee import SqliteDatabase

PRAGMAS = (
    ('foreign_keys', 1),
    ('journal_mode', 'WAL'),
)

db = SqliteDatabase(None, pragmas=PRAGMAS)


def setup_db(db_file):
    global db
    db.init(db_file)
