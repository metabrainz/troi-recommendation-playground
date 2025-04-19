import datetime
from troi import Recording, Playlist, PipelineError
import logging

logger = logging.getLogger(__name__)

class PrintRecordingList:
    """
        Print a list of recordings in a sane matter intended to fit on a reasonably sized screen.
        It prints recording name and artist name always, and year, bpm, listen_count or moods
        if they are found in the first recording.
    """

    def __init__(self):
        super().__init__()
        self.print_year = False
        self.print_bpm = False
        self.print_listen_count = False
        self.print_moods = False
        self.print_genre = False
        self.print_latest_listened_at = False
        self.print_ranking = False

    def _examine_recording_for_headers(self, recording):
        if getattr(recording, 'year', None) is not None:
            self.print_year = True
        if "listen_count" in getattr(recording, 'listenbrainz', {}):
            self.print_listen_count = True
        if "bpm" in getattr(recording, 'acousticbrainz', {}):
            self.print_bpm = True
        if "moods" in getattr(recording, 'acousticbrainz', {}):
            self.print_moods = True
        if "genres" in getattr(recording, 'musicbrainz', {}) or "tags" in getattr(recording, 'musicbrainz', {}):
            self.print_genre = True
        if "latest_listened_at" in getattr(recording, 'listenbrainz', {}):
            self.print_latest_listened_at = True
        if getattr(recording, 'ranking', None):
            self.print_ranking = True

    def _print_recording(self, recording, year=False, listen_count=False, bpm=False, moods=False, genre=False):
        artist = getattr(recording.artist, 'name', None) or "[missing]"
        if artist == "[missing]":
            artist = self._get_artist_fallback(recording)

        rec_name = getattr(recording, 'name', f"[[ mbid:{getattr(recording, 'mbid', '[[ ]]')[:5] } ]]")
        rec_mbid = getattr(recording, 'mbid', '')[:5]

        print(f"{rec_name:<60} {artist:<50} {rec_mbid:5}", end='')

        if self.print_year and getattr(recording, 'year', None):
            print(f" {recording.year:4}", end='')
        if self.print_ranking and getattr(recording, 'ranking', None):
            print(f" {recording.ranking:.3f}", end='')
        if self.print_listen_count or listen_count:
            print(f" {getattr(recording.listenbrainz, 'listen_count', 0):4}", end='')
        if self.print_bpm or bpm:
            print(f" {getattr(recording.acousticbrainz, 'bpm', 0):3}", end='')
        if self.print_latest_listened_at:
            last_listened = getattr(recording.listenbrainz, 'latest_listened_at', None)
            if last_listened is None:
                print(" never    ", end="")
            else:
                td = datetime.datetime.now() - last_listened
                print(f" {td.days:3} days ", end="")
        if self.print_moods or moods:
            mood_aggressive = getattr(recording.acousticbrainz, 'moods', {}).get("mood_aggressive", 0)
            print(f" mood agg {int(100 * mood_aggressive):3}", end='')
        if self.print_genre or genre:
            genres = getattr(recording.musicbrainz, 'genres', [])
            tags = getattr(recording.musicbrainz, 'tags', [])
            print(f" {', '.join(genres + tags)}", end='')

        print()

    def _get_artist_fallback(self, recording):
        if getattr(recording.artist, 'mbids', None):
            return f"[[ artist_mbids:{','.join(recording.artist.mbids)} ]]"
        if getattr(recording.artist, 'artist_credit_id', None):
            return f"[[ artist_credit_id:{recording.artist.artist_credit_id} ]]"
        return "[[ unknown ]]"

    def print(self, entity):
        try:
            if isinstance(entity, (list, Playlist)) and entity:
                recordings = entity if isinstance(entity, list) else entity.recordings
                if recordings and isinstance(recordings[0], Recording):
                    self._examine_recording_for_headers(recordings[0])

                    print(f"{'Recording':<60} {'Artist':<50} {'MBID':5}", end='')

                    has_artist_mbids = False
                    has_artist_credit_id = False
                    for rec in recordings:
                        if rec.artist:
                            if getattr(rec.artist, 'mbids', None):
                                has_artist_mbids = True
                            if getattr(rec.artist, 'artist_credit_id', None):
                                has_artist_credit_id = True

                    if has_artist_mbids:
                        print(f" {'Artist MBIDs':<20}", end='')
                    if has_artist_credit_id:
                        print(f" {'Credit ID':8}", end='')
                    if self.print_year:
                        print(f" {'Year':4}", end='')
                    if self.print_ranking:
                        print(f" {'Rank':5}", end='')
                    if self.print_listen_count:
                        print(f" {'Lis#':4}", end='')
                    if self.print_bpm:
                        print(f" {'BPM':3}", end='')
                    if self.print_latest_listened_at:
                        print(f" {'LastList':9}", end='')
                    if self.print_moods:
                        print(f" {'Mood Agg':11}", end='')
                    if self.print_genre:
                        print(f" {'Genres/Tags':<30}", end='')
                    print()
                    print("-" * 120)

        except Exception as e:
            logger.exception(f"Error occurred while printing: {e}")

        if isinstance(entity, Recording):
            self._examine_recording_for_headers(entity)
            self._print_recording(entity)
            return

        for rec in entity:
            self._examine_recording_for_headers(rec)

        if isinstance(entity, list) and isinstance(entity[0], Recording):
            for rec in entity:
                self._print_recording(rec)

        if isinstance(entity, Playlist):
            for rec in entity.recordings:
                self._print_recording(rec)

        raise PipelineError("You must pass a Recording or list of Recordings or a Playlist to print.")
