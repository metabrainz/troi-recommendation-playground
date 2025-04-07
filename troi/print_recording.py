import datetime
from troi import Recording, Playlist, PipelineError
from prettytable import PrettyTable

class PrintRecordingList():
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
        if recording.year is not None:
            self.print_year = True
        if "listen_count" in recording.listenbrainz:
            self.print_listen_count = True
        if "bpm" in recording.acousticbrainz:
            self.print_bpm = True
        if "moods" in recording.acousticbrainz:
            self.print_moods = True
        if "genres" in recording.musicbrainz or "tags" in recording.musicbrainz:
            self.print_genre = True
        if "latest_listened_at" in recording.listenbrainz:
            self.print_latest_listened_at = True
        if recording.ranking:
            self.print_ranking = True

    def _print_recording(self, recording, year=False, listen_count=False, bpm=False, moods=False, genre=False):
        if recording.artist is None:
            artist = "[missing]"
        elif recording.artist.name is None:
            if recording.artist.mbids is not None:
                artist = "[[ artist_mbids:%s ]]" % ",".join(recording.artist.mbids)
            elif recording.artist.artist_credit_id is not None:
                artist = "[[ artist_credit_id:%d ]]" % (recording.artist.artist_credit_id)
            else:
                artist = "[[ unknown ]]"
        else:
            artist = recording.artist.name
        if recording.name is None:
            rec_name = "[[ mbid:%s ]]" % recording.mbid
        else:
            rec_name = recording.name
        rec_mbid = recording.mbid[:5] if recording.mbid else "[[ ]]"
        print("%-60s %-50s %5s" % (rec_name[:59], artist[:49], rec_mbid), end='')

        if recording.artist is not None:
            if recording.artist.mbids is not None:
                print(" %-20s" % ",".join([ mbid[:5] for mbid in recording.artist.mbids ]), end='')
            if recording.artist.artist_credit_id is not None:
                print(" %8d" % recording.artist.artist_credit_id, end='')

        if self.print_year and recording.year is not None:
            print(" %d" % recording.year, end='')
        if self.print_ranking:
            print(" %.3f" % recording.ranking, end='')
        if self.print_listen_count or listen_count:
            print(" %4d" % recording.listenbrainz['listen_count'], end='')
        if self.print_bpm or bpm:
            print(" %3d" % recording.acousticbrainz['bpm'], end='')
        if self.print_latest_listened_at:
            if recording.listenbrainz["latest_listened_at"] is None:
                print(" never    ", end="")
            else:
                now = datetime.datetime.now()
                td = now - recording.listenbrainz["latest_listened_at"]
                print(" %3d days " % td.days, end="")
        if self.print_moods or moods:
            print(" mood agg %3d" % int(100 * recording.acousticbrainz['moods']["mood_aggressive"]), end='')
        if self.print_genre or genre:
            print(" %s" % ",".join(recording.musicbrainz.get("genres", [])), end='')
            print(" %s" % ",".join(recording.musicbrainz.get("tags", [])), end='')

        print()

    def print(self, entity):
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
        if self.print_latest_listened_at:
            headers.append("Days Since Last Listen")
        if self.print_moods:
            headers.append("Mood Aggressive")
        if self.print_genre:
            headers.append("Genres/Tags")
        table.field_names = headers

        def add_recording_to_table(recording):
            row = [
                recording.name if recording.name else "[[ mbid:%s ]]" % recording.mbid,
                recording.artist.name if recording.artist and recording.artist.name else "[missing]",
                recording.mbid[:5] if recording.mbid else "[[ ]]"
            ]
            if self.print_year and recording.year is not None:
                row.append(recording.year)
            if self.print_ranking:
                row.append("%.3f" % recording.ranking)
            if self.print_listen_count:
                row.append(recording.listenbrainz.get('listen_count', 0))
            if self.print_bpm:
                row.append(recording.acousticbrainz.get('bpm', 0))
            if self.print_latest_listened_at:
                if recording.listenbrainz.get("latest_listened_at") is None:
                    row.append("never")
                else:
                    now = datetime.datetime.now()
                    td = now - recording.listenbrainz["latest_listened_at"]
                    row.append("%d days" % td.days)
            if self.print_moods:
                row.append("mood agg %d" % int(100 * recording.acousticbrainz['moods'].get("mood_aggressive", 0)))
            if self.print_genre:
                genres = recording.musicbrainz.get("genres", [])
                tags = recording.musicbrainz.get("tags", [])
                row.append(", ".join(genres + tags))

            table.add_row(row)

        if isinstance(entity, Recording):
            self._examine_recording_for_headers(entity)
            add_recording_to_table(entity)
        elif isinstance(entity, list) and all(isinstance(rec, Recording) for rec in entity):
            for rec in entity:
                self._examine_recording_for_headers(rec)
                add_recording_to_table(rec)
        elif isinstance(entity, Playlist):
            for rec in entity.recordings:
                self._examine_recording_for_headers(rec)
                add_recording_to_table(rec)
        else:
            raise PipelineError("You must pass a Recording or list of Recordings or a Playlist to print.")

        print(table)
