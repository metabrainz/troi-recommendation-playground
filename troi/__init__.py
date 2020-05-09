import enum

class EntityEnum(enum.Enum): 
    '''
        Defines the various MusicBrainz entities. Not all types have been defined,
        just a few that we will likely use before too long.
    '''
    artist = "artist"
    release_group = "release-group"
    release = "relase"
    recording = "recording"


class Entity(object):

    def __init__(self, etype = None , id = "", name = "", metadata = None):

        # define the domain of the metadata. At first, just MusicBrainz, but other
        # domains might be added later, such as a Spotify domain
        self.domain = "musicbrainz"

        # The type of this entity
        self.type = etype

        # The canonical ID of this entity.
        self.id = id

        # The name of this entity, if applicable
        self.name = name

        # A collection of metadata for this object. If a component has some metdata available
        # about this entity, it should write that metadata into this dict. This dict will
        # have contain string keys, for each domain that has metadata available. Each domain
        # will define they keys and subkeys of their own metadata space.

        if not metadata:
            self.metadata = { 'musicbrainz' : {}, 'listenbrainz' : {}, 'acousticbrainz' : {} }
        else:
            self.metadata = metadata

    @property
    def musicbrainz(self):
        return self.metadata['musicbrainz']

    @property
    def listenbrainz(self):
        return self.metadata['listenbrainz']

    @property
    def acousticbrainz(self):
        return self.metadata['acousticbrainz']

    def __str__(self):
        return "<Entity(%s, %s, '%s')>" % (self.type, self.id, self.name)
