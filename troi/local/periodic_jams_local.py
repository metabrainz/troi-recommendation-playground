import logging

from troi.content_resolver.lb_radio import ListenBrainzRadioLocal
from troi.patches.periodic_jams_local import PeriodicJamsLocalPatch

logger = logging.getLogger(__name__)


class PeriodicJamsLocal(ListenBrainzRadioLocal):
    '''
       Generate local playlists against a music collection available via subsonic.
    '''

    def __init__(self, user_name, match_threshold, quiet):
        ListenBrainzRadioLocal.__init__(self, quiet)
        self.user_name = user_name
        self.match_threshold = match_threshold
        self.quiet = quiet
        self._patch = None

    @property
    def patch(self):
        return self._patch

    def generate(self):
        """
           Generate a periodic jams playlist
        """
    
        self.patch = PeriodicJamsLocalPatch({
            "user_name": self.user_name,
            "quiet": self.quiet,
            "debug": True,
            "min_recordings": 1
        })

        # Now generate the playlist
        try:
            playlist = self.patch.generate_playlist()
        except RuntimeError as err:
            logger.info(f"LB Radio generation failed: {err}")
            return None

        if playlist is None:
            raise RuntimeError("Your prompt generated an empty playlist.")

        # Resolve any tracks that have not been resolved to a subsonic_id or a local file
        self.resolve_playlist(self.match_threshold, playlist)

        return playlist
