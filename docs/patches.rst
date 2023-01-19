.. _patches:

Patches
========

We have a few patches that ship with Troi -- please note that not all of them might be documented here. Some
are still in development or for internal use; we're keeping them there as examples that might help others learn
how to use Troi.

Patches can be found in the *troi/patches* directory.

Area Random Recordings
----------------------

**area-random-recordings**

Given a geograpic area (defined in terms of an area in MusicBrainz) and start/end year, choose random tracks
from this given country and return a playlist of these tracks.


Daily Jams
----------

**daily-jams**

This is our first attempt to create recommended playlists for our users. Daily Jams is a playlist designed 
for the user to put on in the background and to "just have some good tunes without having to think". It should
be all feel-good tracks with nothing new being introduced.

You can create your own daily jams from this patch.

Playlist from MBIDs
-------------------

**playlist-from-mbids**

Given a list of MBIDs, make a playlist from it. Useful for converting a list of MBIDs and to a playlist and then
submitting that playlist to ListenBrainz.

Recommendations to Playlist
---------------------------

**recs-to-playlist**

Fetch ListenBrainz recommended tracks and upload them to ListenBrainz as a playlist.

Weekly Flashback Jams
---------------------

**weekly-flashback-jams**

Generate playlists for past decades based on your listening history.


World Trip
----------

**world-trip**

Given a continent and whether to sort the playlist via longitude or latitude, generate a playlist with tracks
from that continent. 
