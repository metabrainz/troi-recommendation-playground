#!/usr/bin/env python3

import importlib
import inspect
import os
import sys
import click

import troi


def discover_patches(patch_dir):

    patch_dict = {}
    for path in os.listdir(patch_dir):
        if path in ['.', '..']:
            continue

        if path.endswith(".py"):
            print("import %s" % path)
            try:
                patch = importlib.import_module(patch_dir + "." + path[:-3])
            except ImportError as err:
                print("Cannot import %s, skipping: %s" % (path, str(err)))
                continue

            for member in inspect.getmembers(patch):
                if inspect.isclass(member[1]):
                    p = member[1]()
                    patch_dict[p.slug()] = member[1]

    print(patch_dict)

discover_patches("patches")
