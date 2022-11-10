import importlib
import inspect
import os
import traceback
import sys

import troi.patch


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


def recursively_update_dict(source, overrides):
    """ Updates the `source` dictionary in place and in a recursive fashion. That is unlike
    dict1.update(dict2) which would simply replace values of keys even in case one of the
    values is dict, this method will attempt to merge the nested dicts.

    Eg: dict1 - {"a": {"b": 1}}, dict2 - {"a": {"c": 2}}
    dict1.update(dict2) - {"a": {"c": 2}}
    recursively_update_dict(dict1, dict2) - {"a": {"b": 1, "c": 2}}
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and value:
            source[key] = recursively_update_dict(source.get(key, {}), value)
        else:
            source[key] = overrides[key]
    return source

