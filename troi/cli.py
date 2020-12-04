#!/usr/bin/env python3

import sys
import click
import pytest

import troi
import troi.playlist
import troi.utils
from troi.patches.ab_similar_recordings import ABSimilarRecordingsPatch


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
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def playlist(patch, debug, echo, save, token, args):
    """Generate a playlist using a patch"""

    patchname = patch
    patches = troi.utils.discover_patches()
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    patch = patches[patch](debug)

    context = patch.parse_args.make_context(patchname, list(args))
    pipelineargs = context.forward(patch.parse_args)
    pipeline = patch.create(pipelineargs)

    try:
        playlist = troi.playlist.PlaylistElement()
        playlist.set_sources(pipeline)
        playlist.generate()
    except troi.PipelineError as err:
        print("Failed to generate playlist: %s" % err,
              file=sys.stderr)
        return

    if token:
        mbids = playlist.submit(token)
        if len(mbids) == 1:
            print("Submitted playlist: %s" % mbids[0])
        else:
            print("Submitted playlists:", mbid)

    if save:
        playlist.save()
        print("playlist saved.")

    if echo:
        playlist.print()

    if not echo and not save and not token:
        if len(playlist.playlists) == 0:
            print("No playlists where generated. :(")
        elif len(playlist.playlists) == 1:
            print("A playlist with %d tracks was generated." % len(playlist.playlists[0].recordings))
        else:
            print("%d playlists were generated." % len(playlist.playlists))

        print("\nBut, you didn't tell me what to do with it, so I discarded it. (hint: use --submit or --print)")


@cli.command(name="list")
def list_patches():
    """List all available patches"""
    patches = troi.utils.discover_patches()

    print("Available patches:")
    for slug in patches or []:
        print("  %s: %s" % (slug, patches[slug]().description()))


@cli.command()
@click.argument("patch", nargs=1)
def info(patch):
    """Get info for a given patch"""
    patches = troi.utils.discover_patches()
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    apatch = patches[patch]
    context = click.Context(apatch.parse_args, info_name=patch)
    click.echo(apatch.parse_args.get_help(context))


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def test(args):
    """Run unit tests"""
    pytest.main(list(args))


if __name__ == "__main__":
    cli()
    sys.exit(0)
