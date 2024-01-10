import pylistenbrainz
import time

auth_token = input('Please enter your auth token: ')

listen = pylistenbrainz.Listen(
    track_name="Fade",
    artist_name="Kanye West",
    release_name="The Life of Pablo",
    listened_at=int(time.time()),
)

client = pylistenbrainz.ListenBrainz()
client.set_auth_token(auth_token)
response = client.submit_single_listen(listen)
assert response['status'] == 'ok'

listen_2 = pylistenbrainz.Listen(
    track_name="Contact",
    artist_name="Daft Punk",
    release_name="Random Access Memories",
    listened_at=int(time.time()),
)

listen_3 = pylistenbrainz.Listen(
    track_name="Get Lucky",
    artist_name="Daft Punk",
    release_name="Random Access Memories",
    listened_at=int(time.time()),
)

response = client.submit_multiple_listens([listen_2, listen_3])
assert response['status'] == 'ok'
