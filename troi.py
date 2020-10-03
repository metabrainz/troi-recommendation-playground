#!/usr/bin/env python3

import importlib
import inspect
import os
import sys
import click

import troi
import troi.playlist


def discover_patches(patch_dir):

    patch_dict = {}
    for path in os.listdir(patch_dir):
        if path in ['.', '..']:
            continue

        if path.endswith(".py"):
            try:
                patch = importlib.import_module(patch_dir + "." + path[:-3])
            except ImportError as err:
                print("Cannot import %s, skipping: %s" % (path, str(err)))
                continue

            for member in inspect.getmembers(patch):
                if inspect.isclass(member[1]):
                    p = member[1]()
                    patch_dict[p.slug()] = member[1]

    return patch_dict


@click.group()
def cli():
    pass

@cli.command()
@click.argument("patch", nargs=1)
def playlist(patch):

    patches = discover_patches("patches")
    if not patch in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch)
        quit()

    patch = patches[patch]()
    pipeline = patch.create()

    playlist = troi.playlist.PlaylistElement()
    playlist.set_sources(pipeline)
    playlist.generate()
    playlist.print()
    print("-- generated playlist with %d recordings. Open playlist by opening playlist.html in your browser." % len(playlist.entities))
    playlist.launch()


@cli.command()
def list():

    patches = discover_patches("patches")

    print("Available patches:")
    for slug in patches:
        print("  ", slug)


def usage(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    cli()
    sys.exit(0)
