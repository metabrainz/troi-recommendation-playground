import click

import troi
from troi import Element, Artist, Recording, Playlist, PipelineError
from troi.listenbrainz.user import UserListElement
from troi.loops import ForLoopElement

from icecream import ic


@click.group()
def cli():
    pass


class PlaylistMultiplexerElement(Element):
    '''
        Multiplex data from multiple streams into one stream
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return []

    def read(self, inputs):
        outputs = []
        for input in inputs:
            for entity in input:
                outputs.append(entity)

        return outputs


class YIMSubmitterElement(Element):
    '''
        Submit playlists to LB for Year in Music
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [[Playlist]]

    @staticmethod
    def outputs():
        return []

    def read(self, inputs):

        for input in inputs:
            for nested in input:
                print(nested.playlists[0].patch_slug, nested.playlists[0].user_name)

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
    @click.argument('user_names', nargs=-1)
    def parse_args(**kwargs):
        """
        Run a patch for a number of users.

        \b
        PATCH_SLUG: The slug of the patch to run.
        USER_NAMES: The list of ListenBrainz user names to run the patch for.
        """

        return kwargs

    @staticmethod
    def inputs():
        return [
                   { "type": str, "name": "patch_slugs", "desc": "List of Troi patches name to execute (separated by comman, no spaces!)", "optional": False },
                   { "type": list, "name": "user_names", "desc": "ListenBrainz user names", "optional": False }
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

    def create(self, inputs, patch_args):
        user_names = inputs["user_names"]

        patch_slugs = [ slug for slug in inputs["patch_slugs"].split(",") ]
        print("Running the following patches:")
        for slug in patch_slugs:
            print("  %s" % slug)

        u = UserListElement(user_names)
        
        for_loop = ForLoopElement(patch_slugs, inputs, patch_args)
        for_loop.set_sources(u)

        m = PlaylistMultiplexerElement()
        m.set_sources(for_loop)

        y = YIMSubmitterElement()
        y.set_sources(m)

        return y
