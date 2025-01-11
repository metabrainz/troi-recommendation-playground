from prettytable import PrettyTable
import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PrintRecordingList:
    def __init__(self, print_year=True, print_ranking=True, print_listen_count=True, print_bpm=True,
                 print_popularity=True, print_latest_listened_at=True, print_moods=True, print_genre=True):
        self.print_year = print_year
        self.print_ranking = print_ranking
        self.print_listen_count = print_listen_count
        self.print_bpm = print_bpm
        self.print_popularity = print_popularity
        self.print_latest_listened_at = print_latest_listened_at
        self.print_moods = print_moods
        self.print_genre = print_genre

    def print(self, playlist):
        for recording in playlist.recordings:
            self._print_recording(recording)

    def _print_recording(self, recording):
        table = PrettyTable()
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

        table.field_names = headers
        row_data = []

        rec_name = recording.name if recording.name else f"[[ mbid:{recording.mbid} ]]"
        artist = recording.artist_credit.name if recording.artist_credit and recording.artist_credit.name else "[missing]"
        rec_mbid = recording.mbid[:5] if recording.mbid else "[[ ]]"

        row_data.extend([rec_name, artist, rec_mbid])

        if self.print_year:
            row_data.append(recording.year if recording.year is not None else "")
        if self.print_ranking:
            row_data.append(f"{recording.ranking:.3f}" if recording.ranking else "")
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

        table.add_row(row_data)
        table.align = "l"
        logger.info("Recording Table:\n" + table.get_string())
        return table

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    class MockRecording:
        def __init__(self, name, artist_credit, mbid, year, ranking, listenbrainz, acousticbrainz, musicbrainz):
            self.name = name
            self.artist_credit = artist_credit
            self.mbid = mbid
            self.year = year
            self.ranking = ranking
            self.listenbrainz = listenbrainz
            self.acousticbrainz = acousticbrainz
            self.musicbrainz = musicbrainz

    class MockPlaylist:
        def __init__(self, recordings):
            self.recordings = recordings

    mock_recordings = [
        MockRecording(
            name="Song 1",
            artist_credit=type("ArtistCredit", (object,), {"name": "Artist 1"})(),
            mbid="abcd1234",
            year=2023,
            ranking=4.5,
            listenbrainz={"listen_count": 25, "latest_listened_at": datetime.datetime(2024, 1, 1)},
            acousticbrainz={"bpm": 120, "moods": {"mood_aggressive": 0.7}},
            musicbrainz={"popularity": 75.2, "genres": ["Rock"], "tags": ["Live"]}
        )
    ]

    mock_playlist = MockPlaylist(recordings=mock_recordings)
    prl = PrintRecordingList()
    prl.print(mock_playlist)
