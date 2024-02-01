from peewee import *
from troi.content_resolver.model.database import db


class Directory(Model):
    """
    Basic metadata information about a recording on disk (a track).
    """

    class Meta:
        database = db

    id = AutoField()
    dir_path = TextField(null=False, unique=True)
    mtime = TimestampField(null=False)

    def __repr__(self):
        return "<Directory('%s')>" % self.dir_path
