from abc import ABC, abstractmethod


class Entity(ABC):
    """
        This is the base class for entity objects in troi. Each object will have
        a name, mbid, msid attributes which are all optional. There will also be
        three dicts named musicbrainz, listenbrainz and acousticbrainz that will
        contain collected metadata respective of each project. 

        For instance, the musicbrainz dict might have keys that shows the type
        of an artist or the listenbrainz dict might contain the BPM for a track.
        How exactly these dicts will be organized is TDB.
    """
    self __init__(self, musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        self.name = None
        self.mbid = None
        self.msid = None
        self.musicbrainz = musicbrainz
        self.listenbrainz = listenbrainz
        self.acousticbrainz = acousticbrainz

    @property
    def mb(self):
        return self.musicbrainz

    @property
    def lb(self):
        return self.listenbrainz

    @property
    def ab(self):
        return self.acousticbrainz

    def __str__(self):
        return "<Entity()>"


class Artist(Entity):
    """
        The class that represents an artist.
    """
    self __init__(self, name=None, mbid=None, msid=None, musicbrainz=None, 
                  listenbrainz=None, acousticbrainz=None):
        self.name = name
        self.mbid = mbid
        self.msid = msid

    def __str__(self):
        return "<Artist('%s', %s, %s)>" % (self.name, self.mbid, self.msid)


class Release(Entity):
    """
        The class that represents a release.
    """
    self __init__(self, name=None, mbid=None, msid=None, artist=None, 
                  musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        self.artist = None
        self.name = name
        self.mbid = mbid
        self.msid = msid

    @property
    def artist(self):
        return self.artist

    def __str__(self):
        return "<Release('%s', %s, %s)>" % (self.name, self.mbid, self.msid)


class Recording(Entity):
    """
        The class that represents a recording.
    """
    self __init__(self, name=None, mbid=None, msid=None, artist=None, release=None, 
                  musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        self.artist = None
        self.release = None
        self.name = name
        self.mbid = mbid
        self.msid = msid

    @property
    def artist(self):
        return self.artist

    @property
    def release(self):
        return self.release

    def __str__(self):
        return "<Recording('%s', %s, %s)>" % (self.name, self.mbid, self.msid)
