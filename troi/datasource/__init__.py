import abc

class DataSource():
    '''
        This is the base class for implementing a data source component
    '''

    @abc.abstractmethod
    def get(self):
        """
            This base function defines the entry point to the data source. Setting up the data
            source should happen via __init__ and arguments for a specifc batch of listens should
            be given as parameters to get().
        """

        return []
