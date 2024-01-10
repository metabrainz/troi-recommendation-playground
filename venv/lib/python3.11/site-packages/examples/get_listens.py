import pylistenbrainz

client = pylistenbrainz.ListenBrainz()
listens = client.get_listens('iliekcomputers')
for listen in listens:
    print("Track name:", listen.track_name)
    print("Artist name:", listen.artist_name)
