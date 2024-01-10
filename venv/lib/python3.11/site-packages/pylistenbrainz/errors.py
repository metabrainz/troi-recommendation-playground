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

class ListenBrainzException(Exception):
    pass

class ListenBrainzAPIException(ListenBrainzException):
    def __init__(self, status_code, message=None):
        super(ListenBrainzAPIException, self).__init__()
        self.status_code = status_code
        self.message = message


class AuthTokenRequiredException(ListenBrainzException):
    pass


class InvalidAuthTokenException(ListenBrainzException):
    pass


# Exceptions that can be thrown when submitting listens
class InvalidSubmitListensPayloadException(ListenBrainzException):
    pass


class EmptyPayloadException(InvalidSubmitListensPayloadException):
    pass


class UnknownListenTypeException(InvalidSubmitListensPayloadException):
    pass


class TooManyListensException(InvalidSubmitListensPayloadException):
    pass


class ListenedAtInPlayingNowException(InvalidSubmitListensPayloadException):
    pass
