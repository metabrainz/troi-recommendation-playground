import pylistenbrainz

client = pylistenbrainz.ListenBrainz()
listen = client.get_playing_now('iliekcomputers')
assert listen is not None
print("Track name:", listen.track_name)
print("Artist name:", listen.artist_name)
