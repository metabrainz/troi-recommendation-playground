from abc import ABC, abstractmethod

import troi


class Patch(ABC):

    def __init__(self):
        pass

    def inputs(self):
        '''
            This function should return a list of entities or types it expects as input.
            MusicBrainz entities and python base types can all be used.
        '''
        return None

    def slug(self):
        ''' 
            Return the slug for this patch -- this is a URL friendly short identifier
            that can be used to invoke this patch via an HTTP call.

            e.g area-random-recordings
        ''

        return None

    def description(self):
        ''' 
            Return the description for this patch -- this short description (nor more than a paragraph)
            should give the user an idea as to what the patch does.

            e.g "Generate a list of random recordings from a given area."
        ''

        return None

    @abstractmethod
    def run(input_args):
        '''
            The function that will carry out the actual work of constructing
            the data pipeline and generating results.

            Must always return a list of Recordings.
        '''

        return None
