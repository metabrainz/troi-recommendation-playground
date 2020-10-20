#!/usr/bin/env python3

import sys
import click

import troi
import troi.playlist
import troi.utils


@click.group()
def cli():
    pass

@cli.command()
@click.argument("patch", nargs=1)
@click.argument('args', nargs=-1)
@click.option('--debug', '-d', is_flag=True, default=False)
def playlist(patch, args, debug):
    """Generate a playlist using a patch"""
    if debug:
        print("- debug mode on", file=sys.stderr)

    patches = troi.utils.discover_patches("patches")
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    patch = patches[patch]()
    inputs = patch.inputs()

    checked_args = []
    for i, input in enumerate(inputs):
        if not input['optional'] and args[i] is None:
            print("%s: argument '%s' is required." % (patch.slug(), inputs['name']), file=sys.stderr)
            sys.exit(1)
        try:
            value = input['type'](args[i])
        except IndexError:
            continue
        except ValueError as err:
            print("%s: Argument '%s' with type %s is invalid: %s" % (patch.slug(), input['name'], input['type'], err),
                  file=sys.stderr)
            sys.exit(1)

        checked_args.append(value)

    pipeline = patch.create(checked_args)

    try:
        playlist = troi.playlist.PlaylistElement()
        playlist.set_sources(pipeline)
        playlist.generate(debug)
    except RuntimeError as err:
        print("Failed to generate playlist: %s" % err,
              file=sys.stderr)
        return

    playlist.print()
    print("-- generated playlist with %d recordings. Open playlist by opening playlist.html in your browser." % len(playlist.entities))
    playlist.launch()


@cli.command()
def list():
    """List all available patches"""
    patches = troi.utils.discover_patches("patches")

    print("Available patches:")
    for slug in patches:
        print("  %s: %s" % (slug, patches[slug]().description()))


@cli.command()
@click.argument("patch", nargs=1)
def info(patch):
    """Get info for a given patch"""
    patches = troi.util.discover_patches("patches")
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    patch = patches[patch]()
    inputs = patch.inputs()

    print("patch %s" % patch.slug())
    print("  %s" % patch.description())
    print()
    print("  expected inputs:")
    for input in inputs:
        print("     %s, type %s" % (input[1], input[0]))


def usage(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    cli()
    sys.exit(0)