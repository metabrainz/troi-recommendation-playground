from prettytable import PrettyTable
import datetime
import logging
from troi import PipelineError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PrintRecordingList:
    def __init__(self):
        self.print_year = False
        self.print_ranking = False
        self.print_listen_count = False
        self.print_bpm = False
        self.print_popularity = False
        self.print_latest_listened_at = False
        self.print_moods = False
        self.print_genre = False

    def _examine_recording_for_headers(self, recording):
        if hasattr(recording, 'year') and recording.year is not None:
            self.print_year = True

        if hasattr(recording, 'listenbrainz') and "listen_count" in recording.listenbrainz:
            self.print_listen_count = True

        if hasattr(recording, 'acousticbrainz') and "bpm" in recording.acousticbrainz:
            self.print_bpm = True

        if hasattr(recording, 'acousticbrainz') and "moods" in recording.acousticbrainz:
            self.print_moods = True

        if hasattr(recording, 'musicbrainz') and ("genres" in recording.musicbrainz or "tags" in recording.musicbrainz):
            self.print_genre = True

        if hasattr(recording, 'listenbrainz') and "latest_listened_at" in recording.listenbrainz:
            self.print_latest_listened_at = True

        if hasattr(recording, 'ranking') and recording.ranking:
            self.print_ranking = True
        
        if hasattr(recording, 'musicbrainz') and "popularity" in recording.musicbrainz:
            self.print_popularity = True

    def _create_table_headers(self):
        headers = ["Recording Name", "Artist Name", "MBID"]

        if self.print_year:
            headers.append("Year")
        if self.print_ranking:
            headers.append("Ranking")
        if self.print_listen_count:
            headers.append("Listen Count")
        if self.print_bpm:
            headers.append("BPM")
        if self.print_popularity:
            headers.append("Popularity")
        if self.print_latest_listened_at:
            headers.append("Last Listened")
        if self.print_moods:
            headers.append("Mood Aggressive")
        if self.print_genre:
            headers.append("Genres/Tags")

        return headers

    def _get_row_data(self, recording):
        row_data = []

        rec_name = recording.name if hasattr(recording, 'name') and recording.name else f"[[ mbid:{recording.mbid if hasattr(recording, 'mbid') else ''}]]"
        artist = recording.artist_credit.name if hasattr(recording, 'artist_credit') and recording.artist_credit and hasattr(recording.artist_credit, 'name') else "[missing]"
        rec_mbid = recording.mbid[:5] if hasattr(recording, 'mbid') and recording.mbid else "[[ ]]"

        row_data.extend([rec_name, artist, rec_mbid])

        if self.print_year:
            row_data.append(recording.year if hasattr(recording, 'year') and recording.year is not None else "")
        if self.print_ranking:
            row_data.append(f"{recording.ranking:.3f}" if hasattr(recording, 'ranking') and recording.ranking else "")
        if self.print_listen_count:
            row_data.append(recording.listenbrainz.get("listen_count", ""))
        if self.print_bpm:
            row_data.append(recording.acousticbrainz.get("bpm", ""))
        if self.print_popularity:
            row_data.append(f"{recording.musicbrainz.get('popularity', 0.0):.1f}")
        if self.print_latest_listened_at:
            if recording.listenbrainz.get("latest_listened_at") is None:
                row_data.append("never")
            else:
                now = datetime.datetime.now()
                td = now - recording.listenbrainz["latest_listened_at"]
                row_data.append(f"{td.days} days")
        if self.print_moods:
            mood_agg = recording.acousticbrainz.get("moods", {}).get("mood_aggressive", 0)
            row_data.append(f"{int(100 * mood_agg)}")
        if self.print_genre:
            genres = recording.musicbrainz.get("genres", [])
            tags = recording.musicbrainz.get("tags", [])
            row_data.append(", ".join(genres + tags))

        return row_data

    def print(self, entity):
        if hasattr(entity, 'name') and hasattr(entity, 'artist_credit'):
            recordings = [entity]
        elif isinstance(entity, list):
            recordings = entity
        elif hasattr(entity, 'recordings'):
            recordings = entity.recordings
        else:
            raise PipelineError("You must pass a Recording or list of Recordings or a Playlist to print.")

        if recordings:
            self._examine_recording_for_headers(recordings[0])

        table = PrettyTable()
        table.field_names = self._create_table_headers()
        table.align = "l"

        for recording in recordings:
            table.add_row(self._get_row_data(recording))

        logger.info("Recording Table:\n" + table.get_string())
        return table

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")