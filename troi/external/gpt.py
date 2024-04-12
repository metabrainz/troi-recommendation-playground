import json

from troi import Element, Artist, Recording, PipelineError

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

PLAYLIST_PROMPT_PREFIX = "Create a playlist of 50 songs that are suitable for a playlist with the given description:"
PLAYLIST_PROMPT_SUFFIX = "The output should strictly adhere to the following JSON format: the top level JSON object should have three keys, playlist_name to denote the name of the playlist, playlist_description to denote the description of the playlist, and recordings a JSON array of objects where each element JSON object has the recording_name and artist_name keys."


class GPTRecordingElement(Element):
    """ Ask GPT to generate a list of recordings given the playlist description. """

    def __init__(self, api_key, prompt):
        super().__init__()
        if OpenAI is not None:
            self.client = OpenAI(api_key=api_key)
        else:
            raise PipelineError("OpenAI module needs to be installed to use this patch.")
        self.prompt = prompt

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):
        full_prompt = PLAYLIST_PROMPT_PREFIX + " " + self.prompt + " " + PLAYLIST_PROMPT_SUFFIX
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": full_prompt}
            ]
        )

        try:
            playlist = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            raise PipelineError("Cannot parse JSON response from OpenAI: %s" % (response.choices[0].message.content,)) \
                from e

        recordings = []
        for item in playlist["recordings"]:
            artist = Artist(name=item["artist_name"])
            recording = Recording(name=item["recording_name"], artist=artist)
            recordings.append(recording)

        self.local_storage["_playlist_name"] = playlist["playlist_name"]
        self.local_storage["_playlist_desc"] = playlist["playlist_description"]

        return recordings
