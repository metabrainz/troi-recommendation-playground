import datetime
from peewee import *
from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording


class Tag(Model):
    """
       Represents a tag that could be joined to an entity
    """

    class Meta:
        database = db

    id = AutoField()
    name = TextField(null=False, unique=True)

    def __repr__(self):
        return "<Tag('%s')>" % (self.name or "")


class RecordingTag(Model):
    """
      A tag connected to a recording
    """

    class Meta:
        database = db
        table_name = "recording_tag"

    id = AutoField()
    recording = ForeignKeyField(Recording)
    tag = ForeignKeyField(Tag, on_delete="CASCADE")
    last_updated = DateTimeField(null=False, default=datetime.datetime.now)
    entity = TextField(null=False)

    def __repr__(self):
        return "<RecordingTag('%s','%d')>" % (self.tag.name or "", self.recording)
