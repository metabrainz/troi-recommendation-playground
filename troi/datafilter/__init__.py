import abc

class DataFilter():
    '''
        This is the base class for implementing a data filter component
    '''

    @abc.abstractmethod
    def filter(self):
        """
            This base function defines the entry point to the data filter. Setting up the data
            filter should happen via __init__ and arguments for a specifc batch of listens should
            be given as parameters to filter().
        """

        return []
