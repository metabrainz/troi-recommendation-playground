#!/usr/bin/env python3

import sys

import troi
import troi.playlist
import troi.utils


def generate_playlist(patch, debug, echo, save, token, upload, args, created_for, name, desc, min_recordings):
    """
    Generate a playlist using a patch

    patch: The patch slug that identifies the patch to run
    debug: Print debug information or not
    args: Other parameters that might need to be passed to the patch [optional]
    print: This option causes the generated playlist to be printed to stdout.
    save: The save option causes the generated playlist to be saved to disk.
    token: Auth token to use when using the LB API. Required for submitting playlists to the server.
           See https://listenbrainz.org/profile to get your user token.
    upload: Whether or not to submit the finished playlist to the LB server. Token must be set for this to work.
    created-for: If this option is specified, it must give a valid user name and the
                 TOKEN argument must specify a user who is whitelisted as a playlist bot at
                 listenbrainz.org .
    name: Override the algorithms that generate a playlist name and use this name instead.
    desc: Override the algorithms that generate a playlist description and use this description instead.
    min-recordings: The minimum number of recordings that must be present in a playlist to consider it complete.
                    If it doesn't have sufficient numbers of tracks, ignore the playlist and don't submit it.
                    Default: Off, a playlist with at least one track will be considere complete.
    """

    patchname = patch
    patches = troi.utils.discover_patches()
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        return False

    patch = patches[patch](debug)

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

    pipeline = patch.create(pipelineargs, patch_args)
    try:
        playlist = troi.playlist.PlaylistElement()
        playlist.set_sources(pipeline)
        print("Troi playlist generation starting...")
        result = playlist.generate()

        if name:
            playlist.playlists[0].name = name
        if desc:
            playlist.playlists[0].descripton = desc

        print("done.")
    except troi.PipelineError as err:
        print("Failed to generate playlist: %s" % err, file=sys.stderr)
        return False

    if upload and not token:
        print("In order to upload a playlist, you must provide an auth token. Use option --token.")
        return False

    if min_recordings is not None and \
        (len(playlist.playlists) == 0 or len(playlist.playlists[0].recordings) < min_recordings):
        print("Playlist does not have at least %d recordings, stopping." % min_recordings)
        return False

    if result is not None and token and upload:
        for url, _ in playlist.submit(token, created_for):
            print("Submitted playlist: %s" % url)

    if result is not None and save:
        playlist.save()
        print("playlist saved.")

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

    return True


def list_patches():
    """List all available patches"""
    patches = troi.utils.discover_patches()

    print("Available patches:")
    size = max([ len(k) for k in patches])
    for slug in sorted(patches or []):
        print("%s:%s %s" % (slug, " " * (size - len(slug)), patches[slug]().description()))


def patch_info(patch):
    """Get info for a given patch"""
    patches = troi.utils.discover_patches()
    if patch not in patches:
        print("Cannot load patch '%s'. Use the list command to get a list of available patches." % patch,
              file=sys.stderr)
        sys.exit(1)

    apatch = patches[patch]
    context = click.Context(apatch.parse_args, info_name=patch)
    click.echo(apatch.parse_args.get_help(context))
