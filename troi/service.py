class Service:
    """
        Services allow troi users to provide local versions of key search functions
        so that both global (e.g. MusicBrainz) and local search contexts can be used.
        
        Downstream users will be able to provide localized version of search functions
        to provide lists of Recordings that meet certain requirements for playlist inclusion.

        Only one service can be registered for any given service slug at a time. The most
        recently registered service will be use for the next playlist generation.
    """

    def __init__(self, slug):
        self._slug = slug

    @property
    def slug(self):
        return self._slug
