#!/usr/bin/env python3

import click
import io
import subprocess
import ujson

from troi import Entity
from troi.lookup.mb_artist_credit import MBArtistCreditLookup
from troi.lookup.mb_recording import MBRecordingLookup
from troi.datasource.mb_related_artist_credits import MBRelatedArtistCreditsDataSource
from troi.datasource.mb_related_recordings import MBRelatedRecordingsDataSource
import config

def is_homogeneous(entities, type):
    '''
        Check to see if all the items in a list of of the same type
    '''

    if entities:
        return True

    type_set = set()
    for e in entities:
        type_set.add(e.type)

    return len(type_set) == 1 and entities[0].type == type


def make_unique(entities):
    '''
        Make this passed list of entities unique and return the unique list
    '''

    if not is_homogeneous(entities, entities[0].type):
        raise TypeError("entity list not homogenous")

    entity_dict = {}
    for e in entities:
        entity_dict[e.id] = e

    return list(entity_dict.values())

a = '''
{
    "listened_at": 1443521965,
        "track_metadata": {
            "additional_info": {
                "release_mbid": "bf9e91ea-8029-4a04-a26a-224e00a83266",
                "artist_mbids": [
                    "db92a151-1ac2-438b-bc43-b82e149ddd50"
                ],
                "recording_mbid": "98255a8c-017a-4bc7-8dd6-1fa36124572b",
                "tags": [ "you", "just", "got", "rick rolled!"]
            },
            "artist_name": "Rick Astley",
            "track_name": "Never Gonna Give You Up",
            "release_name": "Whenever you need somebody"
        }
}
'''

def serialize_recordings_to_listen_format(entities):

    if not is_homogeneous(entities, "recording"):
        raise TypeError("entity list not homogeneous")

    listens = []
    for e in entities:
        d = {
            'track_metadata' : {
                'artist_name' : e.mb_artist.get('artist_credit_name', ''),
                'track_name' : e.name,
                'release_name' : e.mb_release.get('release_name', ''),
                'additional_info' : {
                    'recording_mbid' : str(e.id)
                }
            }
        }
        listens.append(d)

    return ujson.dumps(listens, indent=4, sort_keys=True)


def make_playlist(recording_mbids):

    # setup components
    datasource_artist_credits = MBRelatedArtistCreditsDataSource(config.DB_CONNECT)
    datasource_recording = MBRelatedRecordingsDataSource(config.DB_CONNECT)

    lookup_artist_credit = MBArtistCreditLookup(config.DB_CONNECT)
    lookup_recording = MBRecordingLookup(config.DB_CONNECT)


    # Create objects for each recording argument and look them up
    recordings = [ Entity("recording", mbid) for mbid in recording_mbids ]
    lookup_recording.lookup(recordings)

    # Fetch the artist credits for each of given tracks and then find related artists for each of them
    artist_credits = [ Entity("artist-credit", recording.mb_recording['artist_credit']) for recording in recordings ]
    related_artist_credits = []
    for ac in artist_credits:
        related_artist_credits.extend(datasource_artist_credits.get(ac, max_items=25))

    related_artist_credits = make_unique(related_artist_credits)
    related_artist_credits = sorted(related_artist_credits, key=lambda e: e.mb_artist['artist_credit_relations_count'], reverse=True)

    related_recordings = []
    for recording in recordings:
        related_recordings.extend(datasource_recording.get(recording))

    related_recordings = make_unique(related_recordings)
    related_recordings = sorted(related_recordings, key=lambda e: e.mb_recording['recording_relations_count'], reverse=True)
    lookup_recording.lookup(related_recordings)


    print("load %d related artist_credits" % (len(related_artist_credits)))
    for e in related_artist_credits[:5]:
        print("  %3d %7d %s" % (e.mb_artist['artist_credit_relations_count'], int(e.id), e.mb_artist['artist_name']))
    print()

    print("load %d related recordings (%s %s)" % (len(related_recordings), 
                                                     str(recording.id)[:6], 
                                                     recording.name))
    for e in related_recordings[:5]:
        print("  %3d %s %-30s %s" % (e.mb_recording['recording_relations_count'], str(e.id)[:6], e.mb_artist['artist_credit_name'][:29], e.name))

    json_playlist = serialize_recordings_to_listen_format(related_recordings[:15])

    with open("playlist.json", "w") as f:
        f.write(json_playlist)

#    with io.StringIO(json_playlist) as jp:
    subprocess.run(['./openpost.py', '-s', '--key listens', 'https://beta.listenbrainz.org/player'], input=json_playlist, encoding="utf-8")


@click.command()
@click.argument("recordings", nargs=-1)
def playlist(recordings):
    make_playlist(recordings)


def usage(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    playlist()
