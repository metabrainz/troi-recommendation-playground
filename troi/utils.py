import importlib
import inspect
import os
import traceback
import sys

from troi import Element, Artist, Recording, Playlist
import troi.patch
from troi.print_recording import PrintRecordingList


def discover_patches():
    """
        Attempt to load patches from the installed patches dir as well as any patches directory in the current dir.
    """

    patches = discover_patches_from_dir("troi.patches.", os.path.join(os.path.dirname(__file__), "patches"))
    try:
        local_patches = discover_patches_from_dir("patches.", "./patches", True)
    except FileNotFoundError:
        local_patches = {}

    return  {**patches, **local_patches}


def discover_patches_from_dir(module_path, patch_dir, add_dot=False):
    """
        Load patches given the appropriate python module path and then file system path. 
        If add_dot = True, add . to the sys.path and then remove it before this function exists.
    """

    if add_dot:
        sys.path.append(".")

    patch_dict = {}
    for path in os.listdir(patch_dir):
        if path in ['.', '..']:
            continue

        if path.startswith("__init__"):
            continue

        if path.endswith(".py"):
            try:
                patch = importlib.import_module(module_path + path[:-3])
            except ImportError as err:
                print("Cannot import %s, skipping:" % (path), file=sys.stderr)
                traceback.print_exc()
                continue

            for member in inspect.getmembers(patch):
                if inspect.isclass(member[1]):
                    if issubclass(member[1], troi.patch.Patch):
                        patch_dict[member[1].slug()] = member[1]

    if add_dot:
        sys.path.pop(-1)

    return patch_dict


def print_entity_list(entities, count=0):
    """
        Print the given entities in a readble fashion. If count is specified,
        print only count number of entities.
    """

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
        super().__init__()

    @staticmethod
    def inputs():
        return [Recording, Playlist]

    @staticmethod
    def outputs():
        return [Recording, Playlist]

    def read(self, inputs):
        for input in inputs:
            pr = PrintRecordingList()
            pr.print(input)

        return inputs[0]
