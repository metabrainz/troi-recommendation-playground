from abc import ABC, abstractmethod
import logging
import random
from typing import Dict

from troi.utils import recursively_update_dict

DEVELOPMENT_SERVER_URL = "https://datasets.listenbrainz.org"


class Element(ABC):
    """
        Base class for elements
    """

    def __init__(self):
        self.sources = []
        self.logger = logging.getLogger(type(self).__name__)

    def log(self, msg):
        '''
            Log a message with the info log level, which is the default for troi.
        '''
        self.logger.info(msg)

    def debug(self, msg):
        '''
            Log a message with debug log level. These messages will only be shown when debugging is enabled.
        '''
        self.logger.debug(msg)

    def set_sources(self, sources):
        """
        """

        if not isinstance(sources, list):
            sources = [ sources ]

        self.sources = sources

        # type check the source
        if len(self.inputs()) > 0:
            for source in sources:
                for output_type in source.outputs() or []:
                    if output_type in self.inputs():
                        break
                    else:
                        raise RuntimeError("Element %s cannot accept %s as input." %
                                           (type(self).__name__, output_type)) 


    def check(self):
        """
            Check to see if the necessary connections are in place
            and that types match correctly.
        """

        if not self.sources:
            raise PipelineError("element %s has no sources defined." % str(type(self)))

        for source in self.sources:
            source.check()


    def generate(self):
        """
            Generate output from the pipeline. This should be called on
            the last element in the pipeline and no where else. At the root
            node generate returns the results, but on interior nodes it
            returns data to be used as input in the next level.
        """

        source_lists = []
        if self.sources:
            for source in self.sources:
                result = source.generate()
                if result is None:
                    return None

                if len(self.inputs()) > 0 and \
                    len(result) > 0 and type(result[0]) not in self.inputs() and \
                    len(source.outputs()) > 0:
                    raise RuntimeError("Element %s was expected to output %s, but actually output %s" % 
                                       (type(source).__name__, source.outputs()[0], type(result[0])))

                source_lists.append(result)

        items = self.read(source_lists)
        if items is None:
            return None

        if len(items) > 0 and type(items[0]) == Playlist:
            print("  %-50s %d items" % (type(self).__name__[:49], len(items[0].recordings or [])))
        else:
            print("  %-50s %d items" % (type(self).__name__[:49], len(items or [])))

        return items

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
    def read(self, source_data_list):
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
        a name, mbid attributes which are all optional. There will also be
        three dicts named musicbrainz, listenbrainz and acousticbrainz that will
        contain collected metadata respective of each project.

        For instance, the musicbrainz dict might have keys that shows the type
        of an artist or the listenbrainz dict might contain the BPM for a track.
        How exactly these dicts will be organized is TDB.
    """
    def __init__(self, ranking=None, musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        self.name = None
        self.mbid = None
        self.musicbrainz = musicbrainz or {}
        self.listenbrainz = listenbrainz or {}
        self.acousticbrainz = acousticbrainz or {}
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
    def __init__(self, name=None, mbids=None, artist_credit_id=None, ranking=None,
                 musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, ranking=ranking, musicbrainz=musicbrainz, listenbrainz=listenbrainz, acousticbrainz=acousticbrainz)
        self.name = name
        self.artist_credit_id = artist_credit_id
        if mbids:
            if not isinstance(mbids, list) and not isinstance(mbids, tuple):
                raise TypeError("Artist mbids must be a list.")
            self.mbids = sorted(mbids)
        else:
            self.mbids = None

    def __str__(self):
        return "<Artist('%s', [%s], %s)>" % (self.name, ",".join(self.mbids or []), self.artist_credit_id)


class Release(Entity):
    """
        The class that represents a release.
    """
    def __init__(self, name=None, mbid=None, artist=None, ranking=None,
                 musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, ranking=ranking, musicbrainz=musicbrainz, listenbrainz=listenbrainz, acousticbrainz=acousticbrainz)
        self.artist = artist
        self.name = name
        self.mbid = mbid

    def __str__(self):
        return "<Release('%s', %s)>" % (self.name, self.mbid)


class Recording(Entity):
    """
        The class that represents a recording.
    """
    def __init__(self, name=None, mbid=None, msid=None, length=None, artist=None, release=None,
                 ranking=None, year=None, spotify_id=None, musicbrainz=None, listenbrainz=None, acousticbrainz=None):
        Entity.__init__(self, ranking=ranking, musicbrainz=musicbrainz, listenbrainz=listenbrainz, acousticbrainz=acousticbrainz)
        self.length = length # track length in ms
        self.artist = artist
        self.release = release
        self.name = name
        self.mbid = mbid
        self.msid = msid
        self.year = year
        self.spotify_id = spotify_id

    def __str__(self):
        return "<Recording('%s', %s, %s)>" % (self.name, self.mbid, self.msid)


class Playlist(Entity):
    """
        The class that represents a playlist, which is nothing more than a [Recording] with metadata. This is
        different from the PlaylistElement, which is normally uses to terminate a pipeline for submitting or
        saving result playlists to disk.

        The arguments are the same as the other entities, except that mbid in this case refers to a playlist_mbid
        and that filename is the suggested filename that this playlist should be saved as, if the user asked to 
        do that and didn't provide a different filename.
    """
    def __init__(self, name=None, mbid=None, filename=None, recordings=None, description=None, ranking=None,
                 year=None, musicbrainz=None, listenbrainz=None, acousticbrainz=None, patch_slug=None, user_name=None,
                 additional_metadata=None):
        Entity.__init__(self, ranking=ranking, musicbrainz=musicbrainz, listenbrainz=listenbrainz, acousticbrainz=acousticbrainz)
        self.name = name
        self.filename = filename
        self.mbid = mbid
        self.recordings = recordings
        self.description = description
        self.patch_slug = patch_slug
        self.user_name = user_name
        self.additional_metadata = additional_metadata

    def __str__(self):
        return "<Playlist('%s', %s, %s)>" % (self.name, self.description, self.mbid)

    def add_metadata(self, metadata: Dict):
        """ Update the playlist's additional metadata recursively """
        if self.additional_metadata is None:
            self.additional_metadata = {}

        recursively_update_dict(self.additional_metadata, metadata)

    def shuffle(self, index=None):
        """ Shuffle the playlists randomly, making no effort to make it "nice" for humans. Screw humans
            and their pesky concept of 'random'."""

        random.shuffle(self.recordings)


class User(Entity):
    """
        The class that represents a ListenBrainz user.
    """
    def __init__(self, user_name=None, user_id=None):
        Entity.__init__(self)
        self.user_name = user_name
        self.user_id = user_id

    def __str__(self):
        return "<User('%s', %d)>" % (self.user_name, self.user_id or -1)


class PipelineError(RuntimeError):
    """
        An exception to be thrown when the pipeline encounters an erorr that is a runtime error and not a
        programming error. The main loop will catch this exception and print an error, but not a stacktrace.
    """
    pass
