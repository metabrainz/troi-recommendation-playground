from collections import defaultdict
import datetime
from operator import itemgetter
from random import shuffle

import troi
from troi import PipelineError, Recording, Playlist


class ArtistCreditFilterElement(troi.Element):
    '''
        Remove recordings if they do or do not belong to a given list of artists.

        :param artist_credit_ids: A list of artist_credit_ids to remove/keep
        :param include: If true, include all tracks with the given artist_credit_id, otherwise remove them.
    '''

    def __init__(self, artist_credit_ids, include=False):
        '''
            Filter a list of Recordings based on their artist_credit_id.
            The default behaviour is to exclude the artists given, but if
            include=True then only the artists in the given list pass
            the filter. Throws PipelineError is not all recordings have
            artist_credit_ids set.
        '''
        super().__init__()
        self.artist_credit_ids = artist_credit_ids
        self.include = include

    @staticmethod
    def inputs():
        return [Recording, Playlist]

    @staticmethod
    def outputs():
        return [Recording, Playlist]

    def read(self, inputs):

        recordings = inputs[0]
        ac_index = {}
        for ac in self.artist_credit_ids:
            try:
                ac_index[ac] = 1
            except KeyError:
                raise PipelineError(self.__name__ + " needs to have all input recordings to have artist.artist_credit_id defined!")

        results = []
        for r in recordings:
            if not r.artist_credit or not r.artist_credit.artist_credit_id:
                continue

            if self.include:
                if r.artist_credit.artist_credit_id in ac_index:
                    results.append(r)
            else:
                if r.artist_credit.artist_credit_id not in ac_index:
                    results.append(r)

        return results


class ArtistCreditLimiterElement(troi.Element):
    '''
        This element examines there passed in recordings and if the count of
        recordings by any one artists exceeds the given limit, excessive recordigns
        are removed. If the flag exclude_lower_ranked is True, and each recording
        has a "ranked" key in the musicbrainz dict, then the lowest
        ranked recordings are removed, otherwise the highest ranked recordings
        are removed. Throws PipelineError is not all recordings have
        artist_credit_ids set.

        :param count: The number of duplicate aritst_credits to allow in the output
        :param exclude_lower_ranked: Remove the lower ranked duplicates, if rankings are present.
    '''

    def __init__(self, count=2, exclude_lower_ranked=True):
        troi.Element.__init__(self)
        self.count = count
        self.exclude_lower_ranked = exclude_lower_ranked

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def _filter(self, recordings):
        """
            Carry out the actual artist limiting.
        """

        ac_index = defaultdict(list)
        all_have_rankings = True
        for rec in recordings:
            try:
                ac_index[rec.artist_credit.artist_credit_id].append((rec.mbid, rec.ranking))
                if rec.ranking is None:
                    all_have_rankings = False
            except KeyError:
                raise PipelineError(self.__name__ + " needs to have all input recordings to have artist.artist_credit_id defined!")

        for key in ac_index:
            if all_have_rankings:
                ac_index[key] = sorted(ac_index[key], key=itemgetter(1), reverse=self.exclude_lower_ranked)
            else:
                shuffle(ac_index[key])
            ac_index[key] = ac_index[key][:self.count]

        pass_recs = []
        for key in ac_index:
            for mbid, ranking in ac_index[key]:
                pass_recs.append(mbid)

        results = []
        for r in recordings:
            if r.mbid in pass_recs:
                results.append(r)

        return results


    def read(self, inputs):
        """
            Determine if recordings or playlists are passed in and call the internal _filter
            function accordingly.
        """

        outputs = []
        for input in inputs:
            if isinstance(input[0], Recording):
                return self._filter(input)
            elif isinstance(input[0], Playlist):
                for playlist in input:
                    playlist.recordings = self._filter(playlist.recordings)
                    outputs.append(playlist)
            else:
                raise PipelineError("ArtistCreditLimiter passed incorrect input types.")

        return outputs


class DuplicateRecordingMBIDFilterElement(troi.Element):
    """
        This Element takes a list of recordings and removes any duplicate recordings
        based on the recording's MBID, preserving the input order.
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        recordings = inputs[0]
        output = []
        seen = set()
        for rec in recordings:
            if rec.mbid not in seen:
                seen.add(rec.mbid)
                output.append(rec)

        return output


class DuplicateRecordingArtistCreditFilterElement(troi.Element):
    """
        This Element takes a list of recordings and removes any duplicate recordings
        based on the recording's name and artist_credit name, preserving the input order.
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        recordings = inputs[0]
        index = {}
        for rec in recordings:
            if rec.name is None or rec.name == "" or rec.artist is None or rec.artist.name is None or rec.artist.name == "":
                continue

            k = rec.name + rec.artist.name
            if k not in index:
                index[k] = rec

        return [ index[k] for k in index ]  


class ConsecutiveRecordingFilterElement(troi.Element):
    """This Element takes a list of recordings and removes consecutive duplicate recordings
    based on the recording's MBID

    For example, a sequence A, A, A, B, B, A, C will be reduced to A, B, A, C
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        recordings = inputs[0]
        output = []
        last_mbid = None
        for rec in recordings:
            if rec.mbid != last_mbid:
                output.append(rec)
            last_mbid = rec.mbid

        return output


class EmptyRecordingFilterElement(troi.Element):
    """This Element takes a list of recordings and removes ones that have an empty name
    or artist.
    """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, input):
        recordings = inputs[0]
        output = []
        for rec in recordings:
            if rec.name is not None and (rec.artist and rec.artist.name is not None) and rec.mbid is not None:
                output.append(rec)

        return output


class YearRangeFilterElement(troi.Element):
    '''
        Filter a list of Recordings based on their year -- the year must be between
        start_year and end_year, otherwise the recording will be filtered out. If no
        end_year is given, keep (or reject in case of inverse) tracks greater or equal
        to start_year. If inverse=True, then keep all Recordings that do no fit into the
        given year range.

        :param start_year: The full start year to filter (inclusive).
        :param end_year: The full end year to filter (inclusive).
        :param inverse: If inverse is True, exclude everything in the year range.
    '''

    def __init__(self, start_year, end_year=None, inverse=False):
        troi.Element.__init__(self)
        self.start_year = start_year
        self.end_year = end_year
        self.inverse = inverse

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]

        results = []
        for r in recordings:
            if not r.year:
                continue

            if self.inverse:
                if r.year < self.start_year:
                    results.append(r)
                elif self.end_year and r.year > self.end_year:
                    results.append(r)
            else:
                if r.year >= self.start_year:
                    if not self.end_year:
                        results.append(r)
                    elif r.year <= self.end_year:
                        results.append(r)

        return results


class GenreFilterElement(troi.Element):
    '''
        Keep recorindgs that have at least one genre in commong
        from the list passed in when this class is created.

        :param genre_list: A list of genre trags to filter out.
    '''

    def __init__(self, genre_list):
        troi.Element.__init__(self)
        self.genre_list = genre_list

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]

        results = []
        for r in recordings:
            if "tags" not in r.musicbrainz:
                continue

            for genre in self.genre_list:
                if genre in r.musicbrainz["tags"]:
                    results.append(r)
                    break

        return results


class LatestListenedAtFilterElement(troi.Element):
    '''
        Filter the recordings according to latest_listened_at field in the lb metadata. 
        If that field is None, treat it as if the user hasn't listened to this track
        recently or at all and keep the track in the list.

        :param min_number_of_days: The number of days that must have passed for a track to be kept.
    '''

    MIN_ITEMS_REQUIRED = 5

    def __init__(self, min_number_of_days=14, keep_unlistened_if_empty=False):
        troi.Element.__init__(self)
        self.min_number_of_days = min_number_of_days
        self.keep_unlistened_if_empty = keep_unlistened_if_empty

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]

        results = []
        now = datetime.datetime.now()
        for r in recordings:
            if "latest_listened_at" in r.listenbrainz and r.listenbrainz["latest_listened_at"] is not None:
                td = now - r.listenbrainz["latest_listened_at"]
                if td.days > self.min_number_of_days:
                    results.append(r)
            else:
                results.append(r)

        if len(results) < self.MIN_ITEMS_REQUIRED and self.keep_unlistened_if_empty:
            self.local_storage["latest_listened_was_empty"] = True
            return recordings

        self.local_storage["latest_listened_was_empty"] = False

        return results


class NeverListenedFilterElement(troi.Element):
    '''
        Remove/keep only recordings if they have not/been listened to.
    '''

    MIN_ITEMS_REQUIRED = 5

    def __init__(self, remove_unlistened=True, keep_unlistened_if_empty=False):
        '''
            Filter the recordings according to latest_listened_at field in the lb metadata. 
            If that field is None, treat it as if the user hasn't listened to this track
            and remove it, or keep it, based on the remove_unlistened parameter.
        '''
        troi.Element.__init__(self)
        self.remove_unlistened = remove_unlistened
        self.keep_unlistened_if_empty = keep_unlistened_if_empty

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]

        results = []
        for r in recordings:
            # has this track never been listened to before?
            if "latest_listened_at" in r.listenbrainz and r.listenbrainz["latest_listened_at"]:
                if self.remove_unlistened:
                    results.append(r)
                else:
                    continue
            else:
                if self.remove_unlistened:
                    continue
                else:
                    results.append(r)

        if len(results) < self.MIN_ITEMS_REQUIRED and self.keep_unlistened_if_empty:
            self.local_storage["never_listened_was_empty"] = True
            return recordings

        self.local_storage["never_listened_was_empty"] = False
        return results


class HatedRecordingsFilterElement(troi.Element):
    """ Remove recordings that have been hated by the user """

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        results = []
        for r in inputs[0]:
            score = r.listenbrainz.get("score", 0)
            if score < 0:
                continue
            results.append(r)
        return results
