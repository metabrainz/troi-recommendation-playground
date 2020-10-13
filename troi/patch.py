from abc import ABC, abstractmethod

import troi


class Patch(ABC):

    def __init__(self):
        pass

    @staticmethod
    def inputs():
        '''
            This function should return a list of dicts that defined the type, name, description and if the 
            argument is optional. MusicBrainz entities and python base types can all be used. Example:
            [
                {
                    "type" : int,
                    "name": "num_recordings",
                    "optional" : True,
                    "desc" : "number of recorings"
                }
            ]
        '''
        return None

    @staticmethod
    def slug():
        ''' 
            Return the slug for this patch -- this is a URL friendly short identifier
            that can be used to invoke this patch via an HTTP call.

            e.g area-random-recordings
        '''

        return None

    @staticmethod
    def description():
        ''' 
            Return the description for this patch -- this short description (not more than a paragraph)
            should give the user an idea as to what the patch does.

            e.g "Generate a list of random recordings from a given area."
        '''

        return None

    @abstractmethod
    def create(input_args):
        '''
            The function creates the data pipeline and then returns it.
        '''

        return None
