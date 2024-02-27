#!/usr/bin/env python3
import logging
import sys

import click

import troi
import troi.playlist
import troi.utils


logger = logging.getLogger(__name__)


def list_patches():
    """
        Print a list of all available patches
    """
    patches = troi.utils.discover_patches()

    logger.info("Available patches:")
    size = max([len(k) for k in patches])
    for slug in sorted(patches or []):
        patch = patches[slug]
        print("%s:%s %s" % (slug, " " * (size - len(slug)), patch.description()))


def patch_info(patch):
    """
        Get info for a given patch

        :param patch: the patch to get info for.
    """

    patches = troi.utils.discover_patches()
    if patch not in patches:
        logger.error("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch)
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
