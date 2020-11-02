import ujson
import openpost

from troi import Recording
from troi.operations import is_homogeneous
import troi


class PlaylistElement(troi.Element):

    def __init__(self):
        super().__init__()
        self.playlist = None
        self.entities = None

    @staticmethod
    def inputs(self):
        return [Recording]

    @property
    def recordings(self):
        return self.entities

    def read(self, inputs):

        entities = inputs[0]
        if not is_homogeneous(entities):
            raise TypeError("entity list not homogeneous")

        listens = []
        for e in entities:
            artist_mbids = [ str(mbid) for mbid in e.artist.mbids or [] ]
            listens.append({
                'listened_at' : 0,
                'track_metadata' : {
                    'artist_name' : e.artist.name if e.artist else "",
                    'track_name' : e.name,
                    'release_name' : e.release.name if e.release else "",
                    'additional_info' : {
                        'recording_mbid' : str(e.mbid),
                        'artist_mbids' : artist_mbids
                    }
                }
            })


        self.entities = entities
        self.playlist = ujson.dumps(listens, indent=4, sort_keys=True)

        return entities


    def print(self):

        if not self.playlist:
            print("[no playlist generated yet]")
            return

        for recording in self.entities:
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
            print("%-60s %-50s" % (rec_name[:59], artist[:49]))


    def launch(self):

        if not self.playlist:
            raise RuntimeError("Playlist has not been generated yet.")

        op = openpost.OpenPost('https://listenbrainz.org/player', keep_file=True, file_name="playlist.html")
        op.add_key('listens', self.playlist)
        op.send_post()
