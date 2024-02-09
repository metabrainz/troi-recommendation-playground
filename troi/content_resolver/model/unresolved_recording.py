import datetime
from peewee import *
from troi.content_resolver.model.database import db


class UnresolvedRecording(Model):
    """
    Table used to track which recordings where resolving failed. This can be used both
    for debugging purposes and to provide the user with a list of 'if you had this
    album, you'd resolve more music' kind of report.
    """

    class Meta:
        database = db
        table_name = "unresolved_recording"

    id = AutoField()
    # Not using the UUIDField here, since it annoyingly removes '-' from the UUID.
    recording_mbid = TextField(null=True, index=True, unique=True)
    lookup_count = IntegerField(null=False, default=1)
    last_updated = DateTimeField(null=False, default=datetime.datetime.now)

    def __repr__(self):
        return "<UnresolvedRecording(%s,%d')>" % (self.recording_mbid, self.count)
