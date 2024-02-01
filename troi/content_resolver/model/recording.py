import datetime
from enum import Enum

from peewee import *
from troi.content_resolver.model.database import db


class FileIdType(Enum):
    FILE_PATH = 0
    SUBSONIC_ID = 1


class FileIdTypeField(IntegerField):
    """
    Enum for file id type
    """

    def __init__(self, *args, **kwargs) -> None:
        super(IntegerField, self).__init__(*args, **kwargs)

    def db_value(self, file_id_type_enum):
        return file_id_type_enum.value

    def python_value(self, db_file_id_type):
        return FileIdType(int(db_file_id_type))


class Recording(Model):
    """
    Basic metadata information about a recording on disk (a track).
    """

    class Meta:
        database = db
        indexes = (
            # create a unique on (file_id, file_id_type)
            (('file_id', 'file_id_type'), True),
        )

    id = AutoField()
    file_id = TextField(null=False, index=True)
    file_id_type = FileIdTypeField(null=False, index=True)
    mtime = TimestampField(null=False)

    artist_name = TextField(null=True)
    release_name = TextField(null=True)
    recording_name = TextField(null=True)

    # Not using the UUIDField here, since it annoyingly removes '-' from the UUID.
    recording_mbid = TextField(null=True, index=True)
    artist_mbid = TextField(null=True, index=True)
    release_mbid = TextField(null=True, index=True)

    duration = IntegerField(null=True)
    track_num = IntegerField(null=True)
    disc_num = IntegerField(null=True)

    def __repr__(self):
        return "<Recording('%s','%s')>" % (self.recording_mbid or "", self.recording_name)


class RecordingMetadata(Model):
    """
    Additional metadata for recordings: popularity. In future additional fields
    like release date and release country could be added to this table.
    """

    class Meta:
        database = db
        table_name = "recording_metadata"

    id = AutoField()
    recording = ForeignKeyField(Recording, backref="metadata")

    popularity = FloatField()
    last_updated = DateTimeField(null=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<RecordingMetadata('%d','%.3f')>" % (self.recording or 0, self.popularity)
