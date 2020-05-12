import enum
from uuid import UUID

class EntityEnum(enum.Enum):
    '''
        Defines the various MusicBrainz entities. Not all types have been defined,
        just a few that we will likely use before too long.
    '''
    artist = "artist"
    artist_credit = "artist-credit"
    release_group = "release-group"
    release = "relase"
    recording = "recording"


class Entity():
    '''
        The core class that represent metadata entity.
    '''

    def __init__(self, etype=None, id=None, name="", metadata=None):

        # define the domain of the metadata. At first, just MusicBrainz, but other
        # domains might be added later, such as a Spotify domain
        self.domain = "musicbrainz"

        # The type of this entity
        if etype and isinstance(etype, Entity):
            self.type = etype
        else:
            try:
                self.type = EntityEnum(etype)
            except ValueError:
                raise ValueError("%s is not a valid EntityType")

        # The canonical ID of this entity.
        if id and isinstance(id, UUID):
            self.id = id
        else:
            try:
                self.id = UUID(id)
            except (ValueError, AttributeError):
                try:
                    self.id = int(id)
                except ValueError:
                    raise ValueError("Entity ids need to be integer or UUID")

        # The name of this entity, if applicable
        self.name = name

        # A collection of metadata for this object. If a component has some metdata available
        # about this entity, it should write that metadata into this dict. This dict will
        # have contain string keys, for each domain that has metadata available. Each domain
        # will define they keys and subkeys of their own metadata space.

        if not metadata:
            self.metadata = {
                'musicbrainz' : {
                    'artist' : {},
                    'release' : {},
                    'recording' : {}
                },
                'listenbrainz' : {},
                'acousticbrainz' : {}
            }
        else:
            self.metadata = metadata

    @property
    def musicbrainz(self):
        return self.metadata['musicbrainz']

    @property
    def mb_artist(self):
        return self.metadata['musicbrainz']['artist']

    @property
    def mb_release(self):
        return self.metadata['musicbrainz']['release']

    @property
    def mb_recording(self):
        return self.metadata['musicbrainz']['recording']

    @property
    def listenbrainz(self):
        return self.metadata['listenbrainz']

    @property
    def acousticbrainz(self):
        return self.metadata['acousticbrainz']

    def __str__(self):
        return "<Entity(%s, %s, '%s')>" % (self.type, self.id, self.name)
