from collections import defaultdict
import importlib
import inspect
import os
import traceback

from troi import Element, Artist, Release, Recording
import troi.patch


def discover_patches(patch_dir):

    patch_dict = {}
    for path in os.listdir(patch_dir):
        if path in ['.', '..']:
            continue

        if path.startswith("__init__"):
            continue

        if path.endswith(".py"):
            try:
                patch = importlib.import_module("troi.patches." + path[:-3])
            except ImportError as err:
                print("Cannot import %s, skipping:" % (path))
                traceback.print_exc()
                continue

            for member in inspect.getmembers(patch):
                if inspect.isclass(member[1]):
                    if issubclass(member[1], troi.patch.Patch):
                        patch_dict[member[1].slug()] = member[1]

    return patch_dict


def print_entity_list(entities, count=0):

    if len(entities) == 0:
        print("[ empty entity list ]")
        return

    if count == 0:
        count = len(entities)

    if isinstance(entities[0], Artist): 
        print("artist list")
        for e in entities[:count]:
            print("  %s %s" % (e.mbid)[:5], e.name)
    elif isinstance(entities[0], Recording): 
        print("recording list")
        for e in entities[:count]:
            if e.artist:
                print("  %s %-41s %s" % (e.mbid[:5], e.name[:80], e.artist.name[:60]))
            else:
                print("  %s %-41s" % (e.mbid[:5], e.name[:80] if e.name else ""))

    print()


class DumpElement(Element):
    """
        Accept whatever and print it out in a reasonably sane manner.
    """

    def __init__(self):
        pass

    @staticmethod
    def inputs():
        return []

    def read(self, inputs, debug=False):

        for input in inputs:
            print_entity_list(input)


class ArtistHistogramElement(Element):
    """
        Calculate and print out an artist histogram based on the tracks read. Makes no changes to the 
        recordings and simply returns what it received.
    """

    def __init__(self):
        pass

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs, debug=False):

        artists = defaultdict(int)
        artist_names = {}
        for rec in inputs[0]:
            artists[rec.artist.artist_credit_id] += 1
            artist_names[rec.artist.artist_credit_id] = rec.artist.name

        print("Artist histogram:")
        for a in sorted(artists.items(), key=lambda artist: artist[1], reverse=True):
            print("%-40s %d" % (artist_names[a[0]][:39], a[1]))
        print()

        return inputs[0]
