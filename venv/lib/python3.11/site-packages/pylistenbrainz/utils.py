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

from pylistenbrainz import errors
from pylistenbrainz.listen import Listen
from pylistenbrainz.listen import LISTEN_TYPES, LISTEN_TYPE_SINGLE, LISTEN_TYPE_IMPORT, LISTEN_TYPE_PLAYING_NOW

def _validate_submit_listens_payload(listen_type, listens):
    if not listens:
        raise errors.EmptyPayloadException("Can't submit empty list of listens")

    if listen_type not in LISTEN_TYPES:
        raise errors.UnknownListenTypeException(f"Invalid listen type: {str(listen_type)}")


    if listen_type != LISTEN_TYPE_IMPORT and len(listens) != 1:
        raise errors.TooManyListensException("Too many listens for listen type %s: %d" % (str(listen_type), len(listens)))

    if listen_type == LISTEN_TYPE_PLAYING_NOW and listens[0].listened_at is not None:
        raise errors.ListenedAtInPlayingNowException("There is a listened_at field in a listen meant to be sent as `playing_now`")


def _convert_api_payload_to_listen(data):
    track_metadata = data['track_metadata']
    additional_info = track_metadata.get('additional_info', {})
    return Listen(
        track_name=track_metadata['track_name'],
        artist_name=track_metadata['artist_name'],
        listened_at=data.get('listened_at'),
        release_name=track_metadata.get('release_name'),
        recording_mbid=additional_info.get('recording_mbid'),
        artist_mbids=additional_info.get('artist_mbids', []),
        release_mbid=additional_info.get('release_mbid'),
        tags=additional_info.get('tags', []),
        release_group_mbid=additional_info.get('release_group_mbid'),
        work_mbids=additional_info.get('work_mbids', []),
        tracknumber=additional_info.get('tracknumber'),
        spotify_id=additional_info.get('spotify_id'),
        listening_from=additional_info.get('listening_from'),
        isrc=additional_info.get('isrc'),
        additional_info=additional_info,
        username=data.get('username'),
        recording_msid=data.get('recording_msid'),
    )
