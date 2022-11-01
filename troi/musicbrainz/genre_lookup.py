import requests

from troi import Element, Recording, PipelineError, Release

MAX_MBIDS_PER_CALL = 20


# TODO: Make this into a generic MB Metadata lookup element
class GenreLookupElement(Element):
    """
        Look up musicbrainz tags for a list of recordings recordings, based on recording mbid.
        Mosly for experimentation for now -- still needs support for adding genre vs tag.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/metadata/recording"

    def __init__(self, count_threshold=3):
        Element.__init__(self)
        self.count_threshold = count_threshold

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        mbid_sets = []
        mbids = []
        for r in recordings:
            mbids.append(r.mbid)
            if len(mbids) >= MAX_MBIDS_PER_CALL:
                mbid_sets.append(mbids)
                mbids = []
        else:
            mbid_sets.append(mbids)
            
        output = []

        data = {}
        for mbid_set in mbid_sets:
            r = requests.get(self.SERVER_URL, params={ "recording_mbids" : ",".join(mbid_set), "inc": "artist release tag" })
            if r.status_code != 200:
                raise PipelineError("Cannot fetch tags from ListenBrainz: HTTP code %d" % r.status_code)

            data = {**data, **r.json()}

        for r in recordings:

            if r.mbid not in data:
                continue

            # Save the whole MB metadata tag info
            r.musicbrainz["tag_metadata"] = data[r.mbid]["tag"]

            genres = []
            tags = []
            for genre in data[r.mbid]["tag"]["recording"]:
                if genre["count"] >= self.count_threshold:
                    if "genre_mbid" in genre:
                        genres.append(genre["tag"])
                    else:
                        tags.append(genre["tag"])

            r.musicbrainz["genre"] = genres
            r.musicbrainz["tag"] = tags

            if r.artist is not None and "artist" in data[r.mbid]["tag"]:
                artist_genres = []
                artist_tags = []
                for genre in data[r.mbid]["tag"]["artist"]:
                    if genre["count"] >= self.count_threshold:
                        if "genre_mbid" in genre:
                            artist_genres.append(genre["tag"])
                        else:
                            artist_tags.append(genre["tag"])

                r.artist.musicbrainz["genre"] = artist_genres
                r.artist.musicbrainz["tag"] = artist_tags

            # We should use this class as the source for MB metadata now
            if r.release is None:
                try:
                    r.release = Release(mbid=data[r.mbid]["release"]["mbid"], name=data[r.mbid]["release"]["name"])
                except KeyError:
                    pass

            if r.release is not None and "release" in data[r.mbid]["tag"]:
                release_genres = []
                release_tags = []
                for genre in data[r.mbid]["tag"]["release_group"]:
                    if genre["count"] >= self.count_threshold:
                        if "genre_mbid" in genre:
                            release_genres.append(genre["tag"])
                        else:
                            release_tags.append(genre["tag"])

                r.release.musicbrainz["genre"] = release_genres
                r.release.musicbrainz["tag"] = release_tags

            output.append(r)

        return output
