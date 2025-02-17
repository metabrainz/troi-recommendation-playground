import logging

from troi import Playlist
from troi.playlist import PlaylistElement
from troi.patches.lb_radio import LBRadioPatch

from troi.content_resolver.tag_search import LocalRecordingSearchByTagService
from troi.content_resolver.artist_search import LocalRecordingSearchByArtistService
from troi.content_resolver.content_resolver import ContentResolver

logger = logging.getLogger(__name__)


class ListenBrainzRadioLocal:
    '''
       Generate local playlists against a music collection available via subsonic.
    '''

    def __init__(self, quiet=False):
        self.quiet = quiet

    def generate(self, mode, prompt, match_threshold):
        """
           Generate a playlist given the mode and prompt. Optional match_threshold, a value from
           0 to 1.0 allows the use to control how well local resolution tracks must match before
           being considered a match.

           Returns a troi playlist object.
        """

        patch = LBRadioPatch({"mode": mode, "prompt": prompt, "quiet": self.quiet, "min_recordings": 1})
        patch.register_service(LocalRecordingSearchByTagService())
        patch.register_service(LocalRecordingSearchByArtistService())

        # Now generate the playlist
        try:
            playlist = patch.generate_playlist()
        except RuntimeError as err:
            logger.info(f"LB Radio generation failed: {err}")
            return None

        if playlist is None:
            return playlist

        # Resolve any tracks that have not been resolved to a subsonic_id or a local file
        self.resolve_playlist(match_threshold, playlist)

        return playlist

    def resolve_playlist(self, match_threshold, playlist):
        """ Attempt to resolve any tracks without local ids to local ids """

        # Find recordings that are missing local ids
        recordings = []
        for recording in playlist.playlists[0].recordings:
            if "subsonic_id" in recording.musicbrainz or "filename" in recording.musicbrainz:
                continue

            recordings.append(recording)

        if not recordings:
            return

        # Use the content resolver to resolve the recordings in situ
        cr = ContentResolver(self.quiet)
        pe = PlaylistElement()
        pe.playlists = [ Playlist(recordings=recordings) ]
        cr.resolve_playlist(match_threshold, pe)

        # Now filter out the tracks that were not matched
        filtered = []
        for rec in playlist.playlists[0].recordings:
            if "subsonic_id" in rec.musicbrainz or "filename" in rec.musicbrainz:
                filtered.append(rec)

        playlist.playlists[0].recordings = filtered
