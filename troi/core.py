#!/usr/bin/env python3

import sys
from typing import Dict

import click

import troi
import troi.playlist
import troi.utils
from troi.patch import Patch

default_patch_args = dict(
    debug=False,
    echo=True,
    save=False,
    token=None,
    upload=False,
    args=None,
    created_for=None,
    name=None,
    desc=None,
    min_recordings=10,
    spotify=None
)


def generate_playlist(patch: Patch, args: Dict):
    """
    Generate a playlist using a patch

    The args parameter is a dict and may containt the following keys:

    * debug: Print debug information or not
    * print: This option causes the generated playlist to be printed to stdout.
    * save: The save option causes the generated playlist to be saved to disk.
    * token: Auth token to use when using the LB API. Required for submitting playlists to the server. See https://listenbrainz.org/profile to get your user token.
    * upload: Whether or not to submit the finished playlist to the LB server. Token must be set for this to work.
    * created-for: If this option is specified, it must give a valid user name and the TOKEN argument must specify a user who is whitelisted as a playlist bot at listenbrainz.org .
    * name: Override the algorithms that generate a playlist name and use this name instead.
    * desc: Override the algorithms that generate a playlist description and use this description instead.
    * min-recordings: The minimum number of recordings that must be present in a playlist to consider it complete. If it doesn't have sufficient numbers of tracks, ignore the playlist and don't submit it. Default: Off, a playlist with at least one track will be considere complete.
    * spotify: if present, attempt to submit the playlist to spotify as well. should be a dict and contain the spotify user id, spotify auth token with appropriate permissions, whether the playlist should be public, private or collaborative. it can also optionally have the existing urls to update playlists instead of creating new ones.

    :param patch: the patch to run
    :param args: the arguments to pass to the patch, may contain one of more of the following keys:

    """

    patch_args = {**default_patch_args, **args}
    pipeline = patch.create(patch_args)
    try:
        playlist = troi.playlist.PlaylistElement()
        playlist.set_sources(pipeline)
        print("Troi playlist generation starting...")
        result = playlist.generate()

        name = patch_args["name"]
        if name:
            playlist.playlists[0].name = name

        desc = patch_args["desc"]
        if desc:
            playlist.playlists[0].descripton = desc

        print("done.")
    except troi.PipelineError as err:
        print("Failed to generate playlist: %s" % err, file=sys.stderr)
        return None

    upload = patch_args["upload"]
    token = patch_args["token"]
    spotify = patch_args["spotify"]
    if upload and not token and not spotify:
        print("In order to upload a playlist, you must provide an auth token. Use option --token.")
        return None

    min_recordings = patch_args["min_recordings"]
    if min_recordings is not None and \
            (len(playlist.playlists) == 0 or len(playlist.playlists[0].recordings) < min_recordings):
        print("Playlist does not have at least %d recordings, stopping." % min_recordings)
        return None

    save = patch_args["save"]
    if result is not None and spotify and upload:
        for url, _ in playlist.submit_to_spotify(
                spotify["user_id"],
                spotify["token"],
                spotify["is_public"],
                spotify["is_collaborative"],
                spotify.get("existing_urls", [])
        ):
            print("Submitted playlist to spotify: %s" % url)

    created_for = patch_args["created_for"]
    if result is not None and token and upload:
        for url, _ in playlist.submit(token, created_for):
            print("Submitted playlist: %s" % url)

    if result is not None and save:
        playlist.save()
        print("playlist saved.")

    echo = patch_args["echo"]
    if result is not None and (echo or not token):
        print()
        playlist.print()

    if not echo and not save and not token:
        if result is None:
            print("Patch executed successfully.")
        elif len(playlist.playlists) == 0:
            print("No playlists were generated. :(")
        elif len(playlist.playlists) == 1:
            print("A playlist with %d tracks was generated." % len(playlist.playlists[0].recordings))
        else:
            print("%d playlists were generated." % len(playlist.playlists))

    return playlist


def list_patches():
    """
        Print a list of all available patches
    """
    patches = troi.utils.discover_patches()

    print("Available patches:")
    size = max([len(k) for k in patches])
    for slug in sorted(patches or []):
        print("%s:%s %s" % (slug, " " * (size - len(slug)), patches[slug]().description()))


def patch_info(patch):
    """
        Get info for a given patch

        :param patch: the patch to get info for.
    """

    patches = troi.utils.discover_patches()
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    apatch = patches[patch]
    cmd = convert_patch_to_command(apatch)
    context = click.Context(cmd, info_name=patch)
    click.echo(cmd.get_help(context))


def convert_patch_to_command(patch):
    """
        Convert patch object to dummy click command to parse args and show help

        :param patch: the patch to get info for.
    """
    def f(**data):
        return data

    f.__doc__ = patch.inputs.__doc__

    for _input in reversed(patch.inputs()):
        args = _input.get("args", [])
        kwargs = _input.get("kwargs", {})
        if _input["type"] == "argument":
            f = click.argument(*args, **kwargs)(f)
        elif _input["type"] == "option":
            f = click.option(*args, **kwargs)(f)
        else:
            click.echo("Patch is invalid, contact patch writer to fix")

    return click.command(no_args_is_help=True)(f)
