from abc import ABC, abstractmethod

import troi


class Patch(ABC):

    def __init__(self):
        pass

    @staticmethod
    def inputs():
        '''
            This function should return a list of tuples of (entity/type, name) it expects as inputs.
            MusicBrainz entities and python base types can all be used.
            e.g [(Recording, "seed_recording"), (Album, "seed_album")]
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
