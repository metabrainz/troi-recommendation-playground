import click

import troi
from troi import Element, Artist, Recording, Playlist, PipelineError
from troi.listenbrainz.user import UserListElement
from troi.loops import ForLoopElement


@click.group()
def cli():
    pass


class PatchRunnerPatch(troi.patch.Patch):
    """
        Run a patch for a list of users.
    """


    def __init__(self, debug):
        troi.patch.Patch.__init__(self, debug)

    @staticmethod
    @cli.command(no_args_is_help=True)
    @click.argument('patch_slug')
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
                   { "type": str, "name": "patch_slug", "desc": "Troi patch name to execute", "optional": False },
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

    def create(self, inputs):
        patch_slug = inputs["patch_slug"]
        user_names = inputs["user_names"]

        u = UserListElement(user_names)
        
        for_loop = ForLoopElement(patch_slug)
        for_loop.set_sources(u)

        return for_loop
