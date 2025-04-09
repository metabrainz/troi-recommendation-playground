import logging

import troi
from abc import ABC, abstractmethod

from troi.playlist import PlaylistElement
from troi.logging_utils import set_log_level
from troi.recording_search_service import RecordingSearchByTagService, RecordingSearchByArtistService

logger = logging.getLogger(__name__)

default_patch_args = dict(save=False,
                          token=None,
                          upload=False,
                          args=None,
                          created_for=None,
                          name=None,
                          desc=None,
                          min_recordings=10,
                          spotify=None,
                          apple_music=None,
                          soundcloud=None,
                          quiet=False)


class Patch(ABC):

    def __init__(self, args):
        self.quiet = False
        self.args = args

        # Dict used for local storage
        self.local_storage = {}

        self.patch_args = {**default_patch_args, **args}
        self.pipeline = self.create(self.patch_args)
        self._set_element_patch(self.pipeline)

        # Setup extensible services
        self.services = {}
        self.register_service(RecordingSearchByTagService())
        self.register_service(RecordingSearchByArtistService())

    @staticmethod
    def inputs():
        """
            This function should return a list of dicts that defined the type (argument or option), args, and kwargs to be passed to the click function. MusicBrainz entities and python base types can all be used. The documentation of the method is used as the help returned by the command. Example:

            .. code-block:: json

                [
                    {
                        "type" : "argument",
                        "args": ["num_recordings"],
                        "kwargs": {
                            "optional": true
                        }
                    }
                ]

        """
        return None

    @staticmethod
    def slug():
        ''' 
            Return the slug for this patch -- this is a URL friendly short identifier that can be used to invoke this patch via an HTTP call.

            e.g area-random-recordings
        '''

        return None

    @staticmethod
    def description():
        '''
            Return the description for this patch -- this short description (not more than a paragraph) should give the user an idea as to what the patch does.

            e.g "Generate a list of random recordings from a given area."
        '''

        return None

    @abstractmethod
    def create(self, input_args):
        """
            The function creates the data pipeline and then returns it. 

            Params:
               input_args: the arguments passed to the patch.
        """
        return None

    def register_service(self, service):
        """
            Register a new service that can provide services to troi patches.

            Only one service can be registered for any given service slug at a time. The most
            recently registered service will be use for the next playlist generation.
        """
        self.services[service.slug] = service

    def get_service(self, slug):
        """
           Given a service slug, return the class registered for this service. 

           Raises IndexError if no such service is registered.
        """
        return self.services[slug]

    def is_local(self):
        """
            If this function returns True, it means that the patch expects to use the local database, so Troi should
            setup the local database before running this patch. Returns False unless overridden by a deriving patch.
        """
        return False

    def post_process(self):
        """
            This function is called once the pipeline has produced its playlist, just before the Playlist object is created.
            This function could be used to inspect data in patch local storage to create the detailed playlist name
            and descriptionm which may not be available when the pipeline is constructed.
        """
        return

    def user_feedback(self):
        """
          Call this function to retrieve a list of strings that give the user feedback about the playlist that was generated, if any.
        """
        try:
            return self.local_storage["user_feedback"]
        except KeyError:
            return []

    def generate_playlist(self):
        """
        Generate a playlist 

        The args parameter is a dict and may containt the following keys:

        * quiet: Do not print out anything
        * save: The save option causes the generated playlist to be saved to disk.
        * token: Auth token to use when using the LB API. Required for submitting playlists to the server. See https://listenbrainz.org/profile to get your user token.
        * upload: Whether or not to submit the finished playlist to the LB server. Token must be set for this to work.
        * created-for: If this option is specified, it must give a valid user name and the TOKEN argument must specify a user who is whitelisted as a playlist bot at listenbrainz.org .
        * name: Override the algorithms that generate a playlist name and use this name instead.
        * desc: Override the algorithms that generate a playlist description and use this description instead.
        * min-recordings: The minimum number of recordings that must be present in a playlist to consider it complete. If it doesn't have sufficient numbers of tracks, ignore the playlist and don't submit it. Default: Off, a playlist with at least one track will be considere complete.
        * spotify: if present, attempt to submit the playlist to spotify as well. should be a dict and contain the spotify user id, spotify auth token with appropriate permissions, whether the playlist should be public, private or collaborative. it can also optionally have the existing urls to update playlists instead of creating new ones.
        * apple_music: if present, attempt to submit the playlist to Apple Music as well. should be a dict and contain the apple developer token, user music token, whether the playlist should be public, private. it can also optionally have the existing urls to update playlists instead of creating new ones.
        * soundcloud: if present, attempt to submit the palylist to soundcloud. should contain soundcloud auth token, whether the playlist should be public or private
        """

        try:
            set_log_level(self.patch_args.get("quiet", False))
            playlist = PlaylistElement()
            playlist.set_sources(self.pipeline)
            logger.info("Troi playlist generation starting...")
            result = playlist.generate(self.quiet)

            name = self.patch_args["name"]
            if name:
                playlist.playlists[0].name = name

            desc = self.patch_args["desc"]
            if desc:
                playlist.playlists[0].descripton = desc

            logger.info("done.")
        except troi.PipelineError as err:
            raise RuntimeError("Playlist generation failed: %s" % err)

        upload = self.patch_args["upload"]
        token = self.patch_args["token"]
        spotify = self.patch_args["spotify"]
        apple_music = self.patch_args["apple_music"]
        soundcloud = self.patch_args["soundcloud"]
        if upload and not token and not spotify and not apple_music and not soundcloud:
            raise RuntimeError("In order to upload a playlist, you must provide an auth token. Use option --token.")

        min_recordings = self.patch_args["min_recordings"]
        if min_recordings is not None and \
                (len(playlist.playlists) == 0 or len(playlist.playlists[0].recordings) < min_recordings):
            raise RuntimeError("Playlist does not have at least %d recordings" % min_recordings)

        save = self.patch_args["save"]
        if result is not None and spotify and upload:
            for url, _ in playlist.submit_to_spotify(
                spotify["user_id"],
                spotify["token"],
                spotify["is_public"],
                spotify["is_collaborative"],
                spotify.get("existing_urls", [])
            ):
                logger.info("Submitted playlist to spotify: %s" % url)

        if result is not None and soundcloud and upload:
            for url, _ in playlist.submit_to_soundcloud(
                soundcloud["token"],
                soundcloud["is_public"],
                soundcloud.get("existing_urls", [])
            ):
                logger.info("Submitted playlist to soundcloud: %s" % url)

        if result is not None and apple_music and upload:
            for url, _ in playlist.submit_to_apple_music(
                apple_music["music_user_token"],
                apple_music["developer_token"],
                apple_music["is_public"],
                apple_music.get("existing_urls", [])
            ):
                logger.info("Submitted playlist to apple music: %s" % url)

        created_for = self.patch_args["created_for"]
        if result is not None and token and upload:
            for url, _ in playlist.submit(token, created_for):
                logger.info("Submitted playlist: %s" % url)

        if result is not None and save:
            playlist.save()
            logger.info("playlist saved.")

        if not self.quiet and result is not None:
            logger.info("")
            playlist.print()

        if len(playlist.playlists) == 0:
            logger.info("No playlists were generated. :(")
        elif len(playlist.playlists) == 1:
            logger.info("A playlist with %d tracks was generated." % len(playlist.playlists[0].recordings))
        else:
            logger.info("%d playlists were generated." % len(playlist.playlists))

        return playlist

    def _set_element_patch(self, element):
        """ 
            Go through the pipeline, setting the patch objects for each Element
        """
        element.set_patch_object(self)
        for src in element.sources:
            self._set_element_patch(src)
