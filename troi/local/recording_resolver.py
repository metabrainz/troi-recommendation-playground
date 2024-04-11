from troi import Element

from troi.content_resolver.content_resolver import ContentResolver
from troi.content_resolver.model.recording import Recording, FileIdType
from troi.content_resolver.model.database import db
from troi import Recording


class RecordingResolverElement(Element):
    """
        This Troi element takes in a list of recordings, which *must* have artist name and recording
        name set and resolves them to a local collection by using the ContentResolver class
    """

    def __init__(self, match_threshold, quiet):
        """ Match threshold: The value from 0 to 1.0 on how sure a match must be to be accepted.
        """
        Element.__init__(self)
        self.match_threshold = match_threshold
        self.resolve = ContentResolver(quiet)

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        # Build the fuzzy index
        lookup_data = []
        for recording in inputs[0]:
            if recording.artist_credit is None or recording.artist_credit.name is None or recording.name is None:
                raise RuntimeError("artist name and recording name are needed for RecordingResolverElement.")

            lookup_data.append({"artist_name": recording.artist_credit.name,
                                "recording_name": recording.name,
                                "recording_mbid": recording.mbid})

        self.resolve.build_index()

        # Resolve the recordings
        resolved = self.resolve.resolve_recordings(lookup_data, self.match_threshold)
        recording_ids = tuple([result["recording_id"] for result in resolved])

        if not recording_ids:
            return []

        # Could also be done with, but for some reason it fails when using IN. <shrug>
        # Recording.select().where(Recording.id.in_(recording_ids))

        # Fetch the recordings to lookup file ids
        query = """SELECT recording.id
                        , file_id
                        , file_id_type
                     FROM recording
                    WHERE """

        where_clause_elements = []
        for id in recording_ids:
            where_clause_elements.append("recording.id = %d" % id)

        where_clause = " or ".join(where_clause_elements)
        query += where_clause

        cursor = db.execute_sql(query)
        recordings = []
        for row in cursor.fetchall():
            recordings.append({"recording_id": row[0],
                               "file_id": row[1],
                               "file_id_type": row[2]})

        # Build indexes
        file_id_index = {}
        for recording in recordings:
            file_id_index[recording["recording_id"]] = (recording["file_id"], recording["file_id_type"])

        # Set the ids into the recordings
        results = []
        for r in resolved:
            file_id, file_id_type = file_id_index[r["recording_id"]]
            recording = inputs[0][r["index"]]
            if file_id_type == FileIdType.SUBSONIC_ID.value:
                recording.musicbrainz["subsonic_id"] = file_id
                results.append(recording)

            if file_id_type == FileIdType.FILE_PATH.value:
                recording.musicbrainz["filename"] = file_id
                results.append(recording)

        return results
