from datetime import datetime

import requests

import troi.filters
import troi.listenbrainz.feedback
import troi.listenbrainz.listens
import troi.listenbrainz.recs
import troi.musicbrainz.recording_lookup
from troi import Playlist, Element, Recording
from troi.musicbrainz.recording import RecordingListElement
from troi.playlist import PlaylistMakerElement, PlaylistShuffleElement

DAYS_OF_RECENT_LISTENS_TO_EXCLUDE = 60  # Exclude tracks listened in last X days from the daily jams playlist


class TaggedRecordingsSourceElement(troi.Element):

    def __init__(self, tags):
        troi.Element.__init__(self)
        self.tags = tags

    def inputs(self):
        return []

    def outputs(self):
        return [Recording]

    def read(self, entities):

        r = requests.post("https://datasets.listenbrainz.org/recording-from-tag/json",
                          json=[{'[tag]': tag } for tag in self.tags])
        return [ Recording(mbid=recording["recording_mbid"]) for recording in r.json() ]


class TagRadioPatch(troi.patch.Patch):
    """
       Make a playlist from recordings that have been tagged with the same tags/genres.
    """

    def __init__(self, debug=False):
        super().__init__(debug)

    @staticmethod
    def inputs():
        """
        Generate a tag/genre radio playlist from selected tags/genres.

        \b
        USER_NAME is a MusicBrainz user name that has an account on ListenBrainz.
        TAGS is a lot of recording level tags to select recordings from.
        """
        return [{
            "type": "argument",
            "args": ["user_name"],
            "kwargs": {
                "required": True,
                "nargs": 1
            }
        }, {
            "type": "argument",
            "args": ["tags"],
            "kwargs": {
                "required": True,
                "nargs": -1
            }
        }]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "tag-radio"

    @staticmethod
    def description():
        return "Generate with recordings from one or more given tags."

    def create(self, inputs):
        user_name = inputs['user_name']
        tags = inputs['tags']

        print("user name: %s" % user_name)
        print("tags: %s" % ",".join(tags))

        source = TaggedRecordingsSourceElement(tags)

        latest_filter = troi.filters.LatestListenedAtFilterElement(DAYS_OF_RECENT_LISTENS_TO_EXCLUDE)
        latest_filter.set_sources(source)

        feedback_lookup = troi.listenbrainz.feedback.ListensFeedbackLookup(user_name)
        feedback_lookup.set_sources(latest_filter)

        recs_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        recs_lookup.set_sources(feedback_lookup)

        hate_filter = troi.filters.HatedRecordingsFilterElement()
        hate_filter.set_sources(recs_lookup)

        tag_list = ", ".join(tags)
        pl_maker = PlaylistMakerElement(name="Tag radio for tags %s" % tag_list,
                                        desc="Randomly selected tracks that have been tagged with '%s'" % tag_list,
                                        patch_slug=self.slug(),
                                        max_num_recordings=50,
                                        max_artist_occurrence=2,
                                        shuffle=True)
        pl_maker.set_sources(hate_filter)

        return pl_maker
