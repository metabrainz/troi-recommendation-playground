import os
from collections import defaultdict
import datetime
import sys

import peewee
import requests

from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, RecordingMetadata
from troi.content_resolver.utils import select_recordings_on_popularity
from troi.recording_search_service import RecordingSearchByTagService
from troi.plist import plist


class LocalRecordingSearchByTagService(RecordingSearchByTagService):
    '''
    Given the local database, search for recordings that meet given tag criteria
    '''

    def __init__(self):
        RecordingSearchByTagService.__init__(self)

    def search(self, tags, operator, pop_begin, pop_end, num_recordings):
        """
        Perform a tag search. Parameters:

        tags - a list of string tags to search for
        operator - a string specifying "or" or "and"
        pop_begin - if many recordings match the above parameters, return only
                        recordings that have a minimum popularity percent score
                        of pop_begin.
        pop_end - if many recordings match the above parameters, return only
                      recordings that have a maximum popularity percent score
                      of pop_end.

        If only few recordings match, the pop_begin and pop_end are
        ignored.
        """

        # Search for all recordings that match the given tags with given operator
        if operator == "or":
            query, params, pop_clause = self.or_search(tags)
        else:
            query, params, pop_clause = self.and_search(tags)

        placeholders = ",".join(("?", ) * len(tags))
        cursor = db.execute_sql(query % (placeholders, pop_clause), params)

        recordings = []
        for rec in cursor.fetchall():
            recordings.append({"recording_mbid": rec[0], "popularity": rec[1], "file_id": rec[2], "file_id_type": rec[3]})

        return select_recordings_on_popularity(recordings, pop_begin, pop_end, num_recordings)

    def or_search(self, tags, min_popularity=None, max_popularity=None):
        """
            Return the sql query that finds recordings using the OR operator
        """

        query = """WITH recording_ids AS (
                        SELECT DISTINCT(recording_id)
                          FROM tag
                          JOIN recording_tag
                            ON recording_tag.tag_id = tag.id
                          JOIN recording
                            ON recording.id = recording_tag.recording_id
                         WHERE name in (%s)
                   )
                       SELECT recording_mbid
                            , popularity AS percent
                            , file_id
                            , file_id_type
                         FROM recording
                         JOIN recording_ids
                           ON recording.id = recording_ids.recording_id
                         JOIN recording_metadata
                           ON recording.id = recording_metadata.recording_id
                           %s
                     ORDER BY popularity DESC"""

        if min_popularity is not None and max_popularity is not None:
            pop_clause = """WHERE popularity >= %.4f AND popularity < %.4f""" % \
                (min_popularity, max_popularity)
        else:
            pop_clause = ""

        return query, tags, pop_clause

    def and_search(self, tags, min_popularity=None, max_popularity=None):
        """
            Return the sql query that finds recordings using the AND operator
        """
        query = """WITH recording_tags AS (
                        SELECT DISTINCT recording.id AS recording_id
                             , tag.name AS tag_name
                          FROM tag
                          JOIN recording_tag
                            ON recording_tag.tag_id = tag.id
                          JOIN recording
                            ON recording.id = recording_tag.recording_id
                         WHERE name in (%s)
                         ORDER BY recording.id
                   ), recording_ids AS (
                       SELECT recording_tags.recording_id
                         FROM recording_tags
                         JOIN recording_metadata
                           ON recording_tags.recording_id = recording_metadata.recording_id
                     GROUP BY recording_tags.recording_id
                       HAVING count(recording_tags.tag_name) = ?
                   )
                       SELECT recording_mbid
                            , popularity AS percent
                            , file_id
                            , file_id_type
                         FROM recording
                         JOIN recording_ids
                           ON recording.id = recording_ids.recording_id
                         JOIN recording_metadata
                           ON recording.id = recording_metadata.recording_id
                           %s
                     ORDER BY popularity DESC"""

        if min_popularity is not None and max_popularity is not None:
            pop_clause = """WHERE popularity >= %.4f AND popularity < %.4f""" % \
                (min_popularity, max_popularity)
        else:
            pop_clause = ""

        return query, (*tags, len(tags)), pop_clause
