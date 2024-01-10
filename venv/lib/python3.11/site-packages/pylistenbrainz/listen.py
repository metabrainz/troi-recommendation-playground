# pylistenbrainz - A simple client library for ListenBrainz
# Copyright (C) 2020 Param Singh <iliekcomputers@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

LISTEN_TYPE_SINGLE = 'single'
LISTEN_TYPE_IMPORT = 'import'
LISTEN_TYPE_PLAYING_NOW = 'playing_now'

LISTEN_TYPES = (
    LISTEN_TYPE_SINGLE,
    LISTEN_TYPE_IMPORT,
    LISTEN_TYPE_PLAYING_NOW,
)

class Listen:
    def __init__(
        self,
        track_name,
        artist_name,
        listened_at=None,
        release_name=None,
        recording_mbid=None,
        artist_mbids=None,
        release_mbid=None,
        tags=None,
        release_group_mbid=None,
        work_mbids=None,
        tracknumber=None,
        spotify_id=None,
        listening_from=None,
        isrc=None,
        additional_info=None,
        username=None,
        recording_msid=None,
    ):
        """ Creates a Listen.

        Needs at least a track name and an artist name.

        :param track_name: the name of the track
        :type track_name: str
        :param artist_name: the name of the artist
        :type artist_name: str
        :param listened_at: the unix timestamp at which the user listened to this listen
        :type listened_at: int, optional
        :param release_name: the name of the MusicBrainz release the track is a part of
        :type release_name: str, optional
        :param recording_mbid: the MusicBrainz ID of this listen's recording
        :type recording_mbid: str, optional
        :param artist_mbids: the MusicBrainz IDs of this listen's artists
        :type artist_mbids: List[str], optional
        :param release_mbid: the MusicBrainz ID of this listen's release
        :type release_mbid: str, optional
        :param tags: a list of user defined tags for this recording, each listen can only have at most 50
            tags and each tag must be shorter than 64 characters.
        :type tags: List[str], optional
        :param release_group_mbid: A MusicBrainz Release Group ID of the release group this
            recording was played from.
        :type release_group_mbid: str, optional
        :param work_mbids: A list of MusicBrainz Work IDs that may be associated with this recording.
        :type work_mbids: List[str], optional
        :param tracknumber: The tracknumber of the recording. This first recording on a release is tracknumber 1.
        :type tracknumber: int, optional
        :param spotify_id: The Spotify track URL associated with this
            recording. e.g.: http://open.spotify.com/track/1rrgWMXGCGHru5bIRxGFV0
        :type spotify_id: str, optional
        :param listening_from: the source of the listen, for example: 'spotify' or 'vlc',
        :type listening_from: str, optional
        :param isrc: The ISRC code associated with the recording.
        :type isrc: str, optional
        :param additional_info: a dict containing any additional fields that should be submitted with the listen.
        :type additional_info: dict, optional
        :param username: the username of the user to whom this listen belongs
        :type username: str, optional
        :param recording_msid: the MSID of this listen's recording
        :type recording_msid: str, optional
        :return: A listen object with the passed properties
        :rtype: Listen
        """
        self.listened_at = listened_at
        self.track_name = track_name
        self.artist_name = artist_name
        self.release_name = release_name
        self.recording_mbid = recording_mbid
        self.artist_mbids = artist_mbids or []
        self.release_mbid = release_mbid
        self.tags = tags or []
        self.release_group_mbid = release_group_mbid or []
        self.work_mbids = work_mbids or []
        self.tracknumber = tracknumber
        self.spotify_id = spotify_id
        self.listening_from = listening_from
        self.isrc = isrc
        self.additional_info = additional_info or {}
        self.username = username
        self.recording_msid = recording_msid


    def _to_submit_payload(self):
        # create the additional_info dict first
        additional_info = self.additional_info
        if self.recording_mbid:
            additional_info['recording_mbid'] = self.recording_mbid
        if self.artist_mbids:
            additional_info['artist_mbids'] = self.artist_mbids
        if self.release_mbid:
            additional_info['release_mbid'] = self.release_mbid
        if self.tags:
            additional_info['tags'] = self.tags
        if self.release_group_mbid:
            additional_info['release_group_mbid'] = self.release_group_mbid
        if self.work_mbids:
            additional_info['work_mbids'] = self.work_mbids
        if self.tracknumber is not None:
            additional_info['tracknumber'] = self.tracknumber
        if self.spotify_id:
            additional_info['spotify_id'] = self.spotify_id
        if self.listening_from:
            additional_info['listening_from'] = self.listening_from
        if self.isrc:
            additional_info['isrc'] = self.isrc

        # create track_metadata now and put additional_info into it if it makes sense
        track_metadata = {
            'track_name': self.track_name,
            'artist_name': self.artist_name,
        }
        if self.release_name:
            track_metadata['release_name'] = self.release_name
        if additional_info:
            track_metadata['additional_info'] = additional_info

        # create final payload and put track metadata into it
        payload = {
            'track_metadata': track_metadata,
        }
        if self.listened_at is not None:
            payload['listened_at'] = self.listened_at

        return payload
