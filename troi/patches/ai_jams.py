import troi.external.gpt
import troi.musicbrainz.mbid_mapping
from troi import Playlist
from troi.patch import Patch
from troi.playlist import PlaylistMakerElement


class AiJamsPatch(Patch):
    """ Generate a playlist using AI from the given prompt. """

    @staticmethod
    def inputs():
        """
        Generate a playlist using AI

        \b
        API_KEY is the OpenAI api key.
        PROMPT is the description of the playlist to generate.
        """
        return [
            {"type": "argument", "args": ["api_key"]},
            {"type": "argument", "args": ["prompt"]}
        ]

    @staticmethod
    def outputs():
        return [Playlist]

    @staticmethod
    def slug():
        return "ai-jams"

    @staticmethod
    def description():
        return "Generate a playlist using AI from the given prompt."

    def create(self, inputs):
        api_key = inputs['api_key']
        prompt = inputs['prompt'].strip()

        ai_recordings_lookup = troi.external.gpt.GPTRecordingElement(api_key, prompt)

        recs_lookup = troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement(remove_unmatched=True)
        recs_lookup.set_sources(ai_recordings_lookup)

        pl_maker = PlaylistMakerElement(
            patch_slug=self.slug(),
            max_num_recordings=50,
            max_artist_occurrence=2,
            shuffle=False
        )
        pl_maker.set_sources(recs_lookup)

        return pl_maker
