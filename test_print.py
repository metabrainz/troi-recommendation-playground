from troi import Recording, ArtistCredit, Playlist
from troi._print_recording import PrintRecordingList  # Corrected import

# Create a sample recording
recording = Recording(
    name="Face to Face",
    mbid="59038056e4501",
    year=2001
)
recording.artist_credit = ArtistCredit(name="Daft Punk")

# Create another recording
recording2 = Recording(
    name="Blood Like Lemonade",
    mbid="9e7ae06710963",
    year=2010
)
recording2.artist_credit = ArtistCredit(name="Morcheeba")

# Create a playlist
playlist = Playlist()
playlist.recordings = [recording, recording2]

# Initialize and use the printer
printer = PrintRecordingList()
printer.print(playlist)
