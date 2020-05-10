import abc

class Lookup():
    '''
        Base class for lookup classes
    '''

    @abc.abstractmethod
    def lookup(self, entity):
        """
            This class/method should be used to load the metadata for an entity.
        """

        return None
