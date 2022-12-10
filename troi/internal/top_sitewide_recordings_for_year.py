from datetime import datetime

from troi import Recording
import troi.listenbrainz.stats
import troi.filters
import troi.sorts
import troi.musicbrainz.recording_lookup
import troi.musicbrainz.mbid_reader
import troi.playlist


class TopSitewideRecordingsPatch(troi.patch.Patch):
    """
        See below for description
    """

    NAME = "Most Listened to Recordings for %d"
    DESC = """<p>
              This playlist is comprised of the top recordings that ListenBrainz users listened to at least once in %d.
              </p>
              <p>
              This playlist serves as an insight to what other users on ListenBrainz are listening to. There is
              very little guarantee that you may like any of these tracks, so we consider this playlist to be a discovery
              playlist.  Because of this, it may require more active listening since it may contain tracks
              that are not fully to your taste.
              </p>
           """

    def __init__(self, debug=False, max_num_recordings=50):
        troi.patch.Patch.__init__(self, debug)
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        """
        Generate the ListenBrainz site wide top recordings for year playlist.

        \b
        FILE_NAME: The filename that contains the recording_mbids for this playlist.
        """
        return [{"type": "argument", "args": ["file_name"]}]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "top-sitewide-recordings-for-year"

    @staticmethod
    def description():
        return "Generate top sitewide recorings for year playlist"

    def create(self, inputs):
        file_name = inputs['file_name']
        year = datetime.now().year

        recs = troi.musicbrainz.mbid_reader.MBIDReaderElement(file_name)

        rec_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
        rec_lookup.set_sources(recs)

        remove_empty = troi.filters.EmptyRecordingFilterElement()
        remove_empty.set_sources(rec_lookup)

        pl_maker = troi.playlist.PlaylistMakerElement(self.NAME % (year,),
                                                      self.DESC % (year,),
                                                      patch_slug=self.slug())
        pl_maker.set_sources(remove_empty)

        shaper = troi.playlist.PlaylistRedundancyReducerElement(max_artist_occurrence=1, max_num_recordings=self.max_num_recordings)
        shaper.set_sources(pl_maker)

        return shaper
