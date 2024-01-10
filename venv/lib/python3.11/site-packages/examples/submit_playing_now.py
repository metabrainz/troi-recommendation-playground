import pylistenbrainz

auth_token = input('Please enter your auth token: ')

listen = pylistenbrainz.Listen(
    track_name="Fade",
    artist_name="Kanye West",
    release_name="The Life of Pablo",
)

client = pylistenbrainz.ListenBrainz()
client.set_auth_token(auth_token)
response = client.submit_playing_now(listen)
assert response['status'] == 'ok'

