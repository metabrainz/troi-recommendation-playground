import ujson
import openpost

from troi import Recording, Playlist
from troi.operations import is_homogeneous
import troi


class PlaylistElement(troi.Element):

    def __init__(self):
        super().__init__()
        self.playlists = []

    @staticmethod
    def inputs():
        return [Recording, Playlist]

    @property
    def recordings(self):
        return self.entities

    def _serialize_to_jspf(self, playlist):

        data = { "creator": "ListenBrainz Troi" }

        if playlist.name:
            data["title"] = playlist.name

        tracks = []
        for e in playlist.recordings:
            track = {}
            artist_mbids = [ str(mbid) for mbid in e.artist.mbids or [] ]
            track["creator"] = e.artist.name if e.artist else ""
            track["album"] = e.release.name if e.release else ""
            track["title"] = e.name
            track["identifier"] = "https://musicbrainz.org/recording/" + str(e.mbid)
            if artist_mbids:
                track["extension"] = {
                    "https://musicbrainz.org#jspf": { 
                        "artist_mbids" : artist_mbids,
                    }
                }
            tracks.append(track)

        data['track'] = tracks
        return ujson.dumps({ "playlist" : data })

    def read(self, inputs):

        outputs = []
        for input in inputs:
            if isinstance(input[0], Recording):
                if not is_homogeneous(input):
                    raise TypeError("entity list not homogeneous")
                self.playlists.append(Playlist(recordings=input))
            elif isinstance(input[0], Playlist):
                if not is_homogeneous(input):
                    raise TypeError("entity list not homogeneous")
                self.playlists.extend(input)
            else:
                raise PipelineError("Playlist passed incorrect input types.")

        return []

    def print(self):

        if not self.playlists:
            print("[no playlist(s) generated yet]")
            return

        for i, playlist in enumerate(self.playlists):
            if playlist.name:
                print("playlist: '%s'" % playlist.name)
            else:
                print("playlist: %d" % i) 

            for recording in playlist.recordings:
                if not recording:
                    print("[invalid Recording]")
                    continue

                if recording.artist is None or recording.artist.name is None:
                    artist = ""
                else:
                    artist = recording.artist.name
                if recording.name is None:
                    rec_name = ""
                else:
                    rec_name = recording.name
                print("%-60s %-50s %s" % (rec_name[:59], artist[:49], str(recording.year or "")))
            print


    def save(self):

        if not self.playlists:
            raise PipelineError("Playlist has not been generated yet.")

        for i, playlist in enumerate(self.playlists):
            filename = playlist.filename or "playlist %03d.jspf" % i
            with open(filename, "w") as f:
                f.write(self._serialize_to_jspf(playlist))

    def launch(self):

        if not self.playlist:
            raise PipelineError("Playlist has not been generated yet.")

        op = openpost.OpenPost('https://listenbrainz.org/player', keep_file=True, file_name="playlist.html")
        op.add_key('listens', self._serialize_to_jspf(self.playlist))
        op.send_post()
