import click

import troi
from troi import Element, Artist, Recording, Playlist, PipelineError
from troi.listenbrainz.yim_user import YIMUserListElement
from troi.loops import ForLoopElement
from troi.playlist import PlaylistElement


@click.group()
def cli():
    pass


class YIMSubmitterElement(Element):
    '''
        Submit playlists to LB for Year in Music
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Playlist]

    @staticmethod
    def outputs():
        return []

    def read(self, inputs):

        if len(inputs) == 0 or len(inputs[0]) == 0:
            return None

        slug = inputs[0][0].patch_slug
        metadata = {"algorithm_metadata": {"source_patch": slug}}
        with open("%s-playlists.json" % slug, "w") as f:
            print("YIMSubmitter:")
            for playlist in inputs[0]:
                if len(playlist.recordings) == 0:
                    continue

                print("  ", playlist.patch_slug, playlist.user_name)
                f.write("%s\n" % playlist.user_name)
                f.write("%s\n" % playlist.mbid)

                playlist.add_metadata(metadata)

                # This is hacky and should be moved to playlist
                playlist_element = PlaylistElement()
                playlist_element.playlists = [playlist]
                playlist_element.save(track_count=5, file_obj=f)
                f.write("\n")

            print("")

        return None


class YIMRunnerPatch(troi.patch.Patch):
    """
        Run a patch for a list of users.
    """


    def __init__(self, debug=False):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('patch_slugs')
    def parse_args(**kwargs):
        """
        Run YIM patch for users in the LB DB

        \b
        PATCH_SLUG: The slug of the patch to run.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [
                   { "type": str, "name": "patch_slugs", "desc": "List of Troi patches name to execute (separated by comman, no spaces!)", "optional": False },
                   { "type": list, "name": "user_names", "desc": "ListenBrainz user names", "optional": True }
               ]

    @staticmethod
    def outputs():
        return []

    @staticmethod
    def slug():
        return "patch-runner"

    @staticmethod
    def description():
        return "Run a given patch for a given list users."

    def create(self, inputs):
        patch_slugs = [ slug for slug in inputs["patch_slugs"].split(",") ]
        print("Running the following patches:")
        for slug in patch_slugs:
            print("  %s" % slug)

        u = YIMUserListElement()
        
        for_loop = ForLoopElement(patch_slugs, inputs)
        for_loop.set_sources(u)

        y = YIMSubmitterElement()
        y.set_sources(for_loop)

        return y
