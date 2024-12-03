#!/usr/bin/env python3
import logging
import sys

import click

from troi.logging_utils import set_log_level
from troi.content_resolver.database import Database
from troi.content_resolver.subsonic import SubsonicDatabase
from troi.content_resolver.metadata_lookup import MetadataLookup
from troi.content_resolver.utils import ask_yes_no_question
from troi.content_resolver.top_tags import TopTags
from troi.content_resolver.duplicates import FindDuplicates
from troi.content_resolver.playlist import write_m3u_playlist, write_jspf_playlist
from troi.content_resolver.unresolved_recording import UnresolvedRecordingTracker

logger = logging.getLogger(__name__)

# TODO: Soon we will need a better configuration file, so we can get rid of this hack
try:
    sys.path.insert(1, ".")
    import config
except ImportError as err:
    config = None

DEFAULT_CHUNKSIZE = 100


def output_playlist(db, playlist, upload_to_subsonic, save_to_m3u, save_to_jspf, dont_ask, subsonic_id=None):
    try:
        recording = playlist.playlists[0].recordings[0]
    except (KeyError, IndexError):
        logger.error("Cannot save empty playlist.")
        return

    if upload_to_subsonic and config:
        if recording and config.SUBSONIC_HOST:
            try:
                _ = recording.musicbrainz["subsonic_id"]
            except KeyError:
                logger.info("Playlist does not appear to contain subsonic ids. Can't upload to subsonic.")
                return

            if dont_ask or ask_yes_no_question("Upload via subsonic? (Y/n)"):
                logger.info("uploading playlist")
                db.upload_playlist(playlist, subsonic_id)
            return

    if save_to_m3u or save_to_jspf:
        try:
            _ = recording.musicbrainz["filename"]
        except KeyError:
            logger.error("Playlist does not appear to contain file paths. Can't write a local playlist.")
            return

    if save_to_m3u:
        if dont_ask or ask_yes_no_question(f"Save to '{save_to_m3u}'? (Y/n)"):
            logger.info("saving playlist")
            write_m3u_playlist(save_to_m3u, playlist)
        return

    if save_to_jspf:
        if dont_ask or ask_yes_no_question(f"Save to '{save_to_jspf}'? (Y/n)"):
            logger.info("saving playlist")
            write_jspf_playlist(save_to_jspf, playlist)
        return

    logger.info("Playlist displayed, but not saved. Use -j, -m or -u options to save/upload playlists.")


def db_file_check(db_file):
    """ Check the db_file argument and give useful user feedback. """

    if not db_file:
        if not config:
            logger.info("Database file not specified with -d (--db_file) argument. Consider adding it to config.py for ease of use.")
            sys.exit(-1)

        if not config.DATABASE_FILE:
            logger.info("config.py found, but DATABASE_FILE is empty. Please add it or use -d option to specify it.")
            sys.exit(-1)

        return config.DATABASE_FILE
    else:
        return db_file


def music_directories_from_config():
    """ Returns list of music directories if any in config file. """

    try:
        return list(set(config.MUSIC_DIRECTORIES))
    except AttributeError:
        return []


@click.group()
def cli():
    pass


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option('--quiet', '-q', 'quiet', help="Do no print out anything", required=False, is_flag=True)
def create(db_file, quiet):
    """Create a new database to track a music collection"""
    set_log_level(quiet)
    db_file = db_file_check(db_file)
    db = Database(db_file, quiet)
    db.create()


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option('-c', '--chunksize', default=DEFAULT_CHUNKSIZE, help="Number of files to add/update at once")
@click.option("-f", "--force", required=False, is_flag=True, default=False, help="Force scanning, ignoring any cache")
@click.option('-q', '--quiet', 'quiet', help="Do no print out anything", required=False, is_flag=True)
@click.argument('music_dirs', nargs=-1, type=click.Path())
def scan(db_file, music_dirs, quiet, chunksize=DEFAULT_CHUNKSIZE, force=False):
    """Scan one or more directories and their subdirectories for music files to add to the collection.
       If no path is passed, check for MUSIC_DIRECTORIES in config instead.
    """
    set_log_level(quiet)
    db_file = db_file_check(db_file)
    db = Database(db_file, quiet)
    db.open()
    if not music_dirs:
        music_dirs = music_directories_from_config()
    db.scan(music_dirs, chunksize=chunksize, force=force)

    # Remove any recordings from the unresolved recordings that may have just been added.
    urt = UnresolvedRecordingTracker()
    releases = urt.cleanup()


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option("-r", "--remove", help="Without this flag, no files are removed.", required=False, is_flag=True, default=True)
@click.option('-q', '--quiet', 'quiet', help="Do no print out anything", required=False, is_flag=True)
def cleanup(db_file, remove, quiet):
    """Perform a database cleanup. Check that files exist and if they don't remove from the index"""
    set_log_level(quiet)
    db_file = db_file_check(db_file)
    db = Database(db_file, quiet)
    db.open()
    db.database_cleanup(remove)


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option('-q', '--quiet', 'quiet', help="Do no print out anything", required=False, is_flag=True)
def metadata(db_file, quiet):
    """Lookup metadata (popularity and tags) for recordings"""
    set_log_level(quiet)
    db_file = db_file_check(db_file)
    db = Database(db_file, quiet)
    db.open()
    lookup = MetadataLookup(quiet)
    lookup.lookup()

    logger.info("\nThese top tags describe your collection:")
    tt = TopTags()
    tt.print_top_tags_tightly(100)


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option('-q', '--quiet', 'quiet', help="Do no print out anything", required=False, is_flag=True)
def subsonic(db_file, quiet):
    """Scan a remote subsonic music collection"""
    set_log_level(quiet)
    db_file = db_file_check(db_file)
    db = SubsonicDatabase(db_file, config, quiet)
    db.open()
    db.sync()


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.argument('count', required=False, default=250)
def top_tags(db_file, count):
    "Display the top most used tags in the music collection. Useful for writing LB Radio tag prompts"
    set_log_level(False)
    db_file = db_file_check(db_file)
    db = Database(db_file, False)
    db.open()
    tt = TopTags()
    tt.print_top_tags_tightly(count)


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
@click.option('-e',
              '--exclude-different-release',
              help="Exclude duplicates that appear on different releases",
              required=False,
              default=False,
              is_flag=True)
@click.option('-v', '--verbose', help="Display extra info about found files", required=False, default=False, is_flag=True)
def duplicates(db_file, exclude_different_release, verbose):
    "Print all the tracks in the DB that are duplicated as per recording_mbid"
    set_log_level(False)
    db_file = db_file_check(db_file)
    db = Database(db_file, False)
    db.open()
    fd = FindDuplicates(db)
    fd.print_duplicate_recordings(exclude_different_release, verbose)


@click.command()
@click.option("-d", "--db_file", help="Database file for the local collection", required=False, is_flag=False)
def unresolved(db_file):
    "Show the top unresolved releases"
    set_log_level(False)
    db_file = db_file_check(db_file)
    db = Database(db_file, False)
    db.open()
    urt = UnresolvedRecordingTracker()
    releases = urt.get_releases()
    urt.print_releases(releases)


cli.add_command(create)
cli.add_command(scan)
cli.add_command(cleanup)
cli.add_command(metadata)
cli.add_command(subsonic)
cli.add_command(top_tags)
cli.add_command(duplicates)
cli.add_command(unresolved)


def usage(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    cli()
    sys.exit(0)
