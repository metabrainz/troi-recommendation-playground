from abc import ABC, abstractmethod


class Element(ABC):
    """
        Base class for elements
    """

    def __init__(self):
        self.next_elements = []

    def connect(self, next_elements):
        """
            This function chains the next Element to the outputs of
            this element. The items in next_elements must correspond in
            type and sequence to the outputs of this element. If the outputs
            function specifies [ Artist, Release] then next_elements must
            contains other elements; the first one must accept a list of artists
            and the second one must accept a list of releases.
        """

        if not isinstance(next_elements, list):
            next_elements = [ next_elements ]

#        if len(self.inputs()) != len(next_elements):
#            raise ValueError("Cannot connect a next element. The number of outputs from " +
#                             "the connecting element must match the number  of next elements.")
#
#        for output, element in zip(self.outputs(), next_elements):


        self.next_elements = next_elements

    def inputs(self):
        """
            Return a list of Artist, Release or Recording classes that define
            the type and number of input lists to this element. 
            e.g. [ Artist, Recording ] means that this element expects
            a list of artists and a list of recordings for inputs.
        """
        return None

    def outputs(self):
        """
            Return a list of Artist, Release or Recording classes that define
            the type and number of output lists returned by this element. 
            e.g. [ Artist, Recording ] means that this element returns
            a list of artists and a list of recordings.
        """
        return None

    @abstractmethod
    def push(self, inputs):
        ''' 
            This method is where the action happens -- when a connected has generated
            data ready for this element to process, it will call push with the 
            expected inputs. This element should carry out its task and then
            call push on its next elements.
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
    def __init__(self, musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        self.name = None
        self.mbid = None
        self.msid = None
        self.musicbrainz = musicbrainz
        self.listenbrainz = listenbrainz
        self.acousticbrainz = acousticbrainz
        self.notes = []

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


class Artist(Entity):
    """
        The class that represents an artist.
    """
    def __init__(self, name=None, mbids=None, msid=None, artist_credit_id=None,
                 musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, musicbrainz, listenbrainz, acousticbrainz)
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
        return "<Artist('%s', [%s], %s)>" % (self.name, ",".join(self.mbids or []), self.msid)


class Release(Entity):
    """
        The class that represents a release.
    """
    def __init__(self, name=None, mbid=None, msid=None, artist=None, 
                  musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, musicbrainz, listenbrainz, acousticbrainz)
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
    def __init__(self, name=None, mbid=None, msid=None, artist=None, release=None, 
                  musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, musicbrainz, listenbrainz, acousticbrainz)
        self.artist = artist
        self.release = release
        self.name = name
        self.mbid = mbid
        self.msid = msid

    def __str__(self):
        return "<Recording('%s', %s, %s)>" % (self.name, self.mbid, self.msid)
