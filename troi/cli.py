#!/usr/bin/env python3

import sys
import click

from troi.utils import discover_patches
from troi.core import generate_playlist, list_patches, patch_info


@click.group()
def cli():
    pass


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('patch', type=str)
@click.option('--debug/--no-debug')
@click.option('--print', '-p', 'echo', required=False, is_flag=True)
@click.option('--save', '-s', required=False, is_flag=True)
@click.option('--token', '-t', required=False, type=click.UUID)
@click.option('--upload', '-u', required=False, is_flag=True)
@click.option('--created-for', '-c', required=False)
@click.option('--name', '-n', required=False)
@click.option('--desc', '-d', required=False)
@click.option('--min-recordings', '-m', type=int, required=False)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def playlist(patch, debug, echo, save, token, upload, args, created_for, name, desc, min_recordings):
    """
    Generate a playlist using a patch

    \b
    PRINT: This option causes the generated playlist to be printed to stdout.
    SAVE: The save option causes the generated playlist to be saved to disk.
    TOKEN: Auth token to use when using the LB API. Required for submitting playlists to the server.
           See https://listenbrainz.org/profile to get your user token.
    UPLOAD: Whether or not to submit the finished playlist to the LB server. Token must be set for this to work.
    CREATED-FOR: If this option is specified, it must give a valid user name and the
                 TOKEN argument must specify a user who is whitelisted as a playlist bot at
                 listenbrainz.org .
    NAME: Override the algorithms that generate a playlist name and use this name instead.
    DESC: Override the algorithms that generate a playlist description and use this description instead.
    MIN-RECORDINGS: The minimum number of recordings that must be present in a playlist to consider it complete.
                    If it doesn't have sufficient numbers of tracks, ignore the playlist and don't submit it.
                    Default: Off, a playlist with at least one track will be considere complete.
    """
    patchname = patch
    patches = discover_patches()
    if patchname not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patchname,
              file=sys.stderr)
        return None

    patch = patches[patchname](debug)

    if args is None:
        args = []
    context = patch.parse_args.make_context(patchname, list(args))
    pipelineargs = context.forward(patch.parse_args)

    patch_args = {
        "echo": echo,
        "save": save,
        "token": token,
        "created_for": created_for,
        "upload": upload,
        "name": name,
        "desc": desc,
        "min_recordings": min_recordings
    }
    patch_args.update(pipelineargs)
    ret = generate_playlist(patch, patch_args)

    sys.exit(0 if ret else -1)


@cli.command(name="list")
def list_patches_cli():
    """List all available patches"""
    ret = list_patches()
    sys.exit(0 if ret else -1)


@cli.command()
@click.argument("patch", nargs=1)
def info(patch):
    """Get info for a given patch"""
    ret = patch_info(patch)
    sys.exit(0 if ret else -1)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def test(args):
    """Run unit tests"""
    import pytest
    pytest.main(list(args))


if __name__ == "__main__":
    cli()
    sys.exit(0)
