import datetime

from troi.logging import info, error
from troi import Recording, Playlist, PipelineError

class PrintRecordingList():
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
        # Look at the first item and decide which columns to show
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
        """ Print out a recording, formatting it nicely to fit in a reasonably sized window.
            The year, listen_count, bpm, mood and genre arguments here can override the settings
            gleaned from the first recording submitted to this class"""


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

        text = "%-60s %-50s %5s" % (rec_name[:59], artist[:49], rec_mbid)

        if recording.artist is not None:
            if recording.artist.mbids is not None:
                text += " %-20s" % ",".join([ mbid[:5] for mbid in recording.artist.mbids ])
            if recording.artist.artist_credit_id is not None:
                text += " %8d" % recording.artist.artist_credit_id

        if self.print_year and recording.year is not None:
            text += " %d" % recording.year
        if self.print_ranking:
            text += " %.3f" % recording.ranking
        if self.print_listen_count or listen_count:
            text += " %4d" % recording.listenbrainz['listen_count']
        if self.print_bpm or bpm:
            text += " %3d" % recording.acousticbrainz['bpm']
        if self.print_latest_listened_at:
            if recording.listenbrainz["latest_listened_at"] is None:
                text += " never    "
            else:
                now = datetime.datetime.now()
                td = now - recording.listenbrainz["latest_listened_at"]
                text += " %3d days " % td.days
        if self.print_moods or moods:
            # TODO: make this print more than agg, but given the current state of moods/coverage...
            text = " mood agg %3d" % int(100 * recording.acousticbrainz['moods']["mood_aggressive"])
        if self.print_genre or genre:
            text = " %s" % ",".join(recording.musicbrainz.get("genres", []))
            text = " %s" % ",".join(recording.musicbrainz.get("tags", []))

        info(text)


    def print(self, entity):
        """ Print out a list(Recording) or list(Playlist). """

        if type(entity) == Recording:
            self._examine_recording_for_headers(entity)
            self._print_recording(entity)
            return

        for rec in entity:
            self._examine_recording_for_headers(rec)

        if type(entity) == list and type(entity[0]) == Recording:
            for rec in entity:
                self._print_recording(rec)

        if type(entity) == Playlist:
            for rec in entity.recordings:
                self._print_recording(rec)

        raise PipelineError("You must pass a Recording or list of Recordings or a Playlist to print.")
