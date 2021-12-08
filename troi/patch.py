import logging
from abc import ABC, abstractmethod


class Patch(ABC):

    def __init__(self, debug=False):
        if debug:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.basicConfig(level=level)
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
    def create(self, input_args, patch_args):
        '''
            The function creates the data pipeline and then returns it. 

            Params:
               input_args: the passed arguments to the pipeline
               patch_args: the arguments passed to the topmost patch.
        '''

        return None
