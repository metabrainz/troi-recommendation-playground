from abc import ABC, abstractmethod


class Element(ABC):
    """
        Base class for elements
    """

    def __init__(self):
        self.sources = []

    def set_sources(self, sources):
        """
        """

        # TODO: add type checking of the pipeline
        if not isinstance(sources, list):
            sources = [ sources ]

        self.sources = sources

    def check(self):
        """
            Check to see if the necessary connections are in place
            and that types match correctly.
        """

        if not self.sources:
            raise RuntimeError("element %s has no sources defined." % str(type(self)))

        for source in self.sources:
            source.check()


    def generate(self, debug=False):
        """
            Generate output from the pipeline. This should be called on
            the last element in the pipeline and no where else. At the root
            node generate returns the results, but on interior nodes it
            returns data to be used as input in the next level.
        """

        source_lists = []
        if self.sources:
            for source in self.sources:
                source_lists.append(source.generate(debug))

        recordings = self.read(source_lists, debug)
        if debug:
            print("- debug %-50s %d items" % (type(self).__name__[:49], len(recordings or [])))

        return recordings

    def run(self):
        """
            This function should be called on the very last element of the
            pipeline to generate output from the timeline. Run will santiy
            check the pipeline first, and then generate output if it can.
        """
        self.check()
        return self.generate()

    @staticmethod
    def inputs():
        """
            Return a list of Artist, Release or Recording classes that define
            the type and number of input lists to this element.
            e.g. [ Artist, Recording ] means that this element expects
            a list of artists and a list of recordings for inputs.
        """
        return None

    @staticmethod
    def outputs():
        """
            Return a list of Artist, Release or Recording classes that define
            the type and number of output lists returned by this element.
            e.g. [ Artist, Recording ] means that this element returns
            a list of artists and a list of recordings.
        """
        return None

    @abstractmethod
    def read(self, source_data_list, debug):
        '''
            This method is where the action happens -- when the consumer wants to
            read data from the pipeline, it calls read() on the last element in
            the pipeline and this casues the while pipeline to generate result.
            If the initializers of other objects in the pipeline are updated,
            calling read() again will generate the set new. Passing True for
            debug should print helpful debug statements about its progress.
        '''

        pass


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
    def __init__(self, ranking=None, musicbrainz={}, listenbrainz={}, acousticbrainz={}):
        self.name = None
        self.mbid = None
        self.msid = None
        self.musicbrainz = musicbrainz
        self.listenbrainz = listenbrainz
        self.acousticbrainz = acousticbrainz
        self.notes = []
        self.ranking = ranking

    @property
    def mb(self):
        return self.musicbrainz

    @property
    def lb(self):
        return self.listenbrainz

    @property
    def ab(self):
        return self.acousticbrainz

    def add_note(self, note):
        '''
            This allows various parts of the pipeline to leave notes/comments in the data/
        '''
        self.notes.append(note)

    def __str__(self):
        return "<Entity()>"


class Area(Entity):
    """
        The class that represents an area.
    """
    def __init__(self, id=id, name=None):
        Entity.__init__(self)
        self.name = name
        self.id = id

    def __str__(self):
        return "<Area('%s', %d)>" % (self.name, self.id)


class Artist(Entity):
    """
        The class that represents an artist.
    """
    def __init__(self, name=None, ranking=None, mbids=None, msid=None, artist_credit_id=None,
                 musicbrainz={}, listenbrainz={}, acousticbrainz={}):
        Entity.__init__(self, ranking, musicbrainz, listenbrainz, acousticbrainz)
        self.name = name
        self.artist_credit_id = artist_credit_id
        if mbids:
            if not isinstance(mbids, list):
                raise TypeError("Artist mbids must be a list.")
            self.mbids = sorted(mbids)
        else:
            self.mbids = None
        self.msid = msid

    def __str__(self):
        return "<Artist('%s', [%s], %s, %s)>" % (self.name, ",".join(self.mbids or []), self.msid, self.artist_credit_id)


class Release(Entity):
    """
        The class that represents a release.
    """
    def __init__(self, name=None, ranking=None, mbid=None, msid=None, artist=None,
                  musicbrainz={}, listenbrainz={}, acousticbrainz={}):
        Entity.__init__(self, ranking, musicbrainz, listenbrainz, acousticbrainz)
        self.artist = artist
        self.name = name
        self.mbid = mbid
        self.msid = msid

    def __str__(self):
        return "<Release('%s', %s, %s)>" % (self.name, self.mbid, self.msid)


class Recording(Entity):
    """
        The class that represents a recording.
    """
    def __init__(self, name=None, ranking=None, mbid=None, msid=None, length=None, artist=None, release=None,
                  musicbrainz={}, listenbrainz={}, acousticbrainz={}):
        Entity.__init__(self, ranking, musicbrainz, listenbrainz, acousticbrainz)
        self.length = length # track length in ms
        self.artist = artist
        self.release = release
        self.name = name
        self.mbid = mbid
        self.msid = msid

    def __str__(self):
        return "<Recording('%s', %s, %s)>" % (self.name, self.mbid, self.msid)


class PipelineError(RuntimeError):
    """
        An exception to be thrown when the pipeline encounters an erorr that is a runtime error and not a
        programming error. The main loop will catch this exception and print an error, but not a stacktrace.
    """
    pass
