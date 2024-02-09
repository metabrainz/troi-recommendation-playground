.. _troi-arguments:

Command line options
====================

Playlist generation options
---------------------------

The full list of command line options for each of the commands is below:

.. click:: troi.cli:cli
   :prog: troi
   :nested: full
   :commands: list, playlist, lb-radio, resolve, weekly-jams, test

Database / content resolution options
-------------------------------------

.. click:: troi.content_resolver.cli:cli
   :prog: troi db
   :nested: full
   :commands: create, scan, subsonic, clean, metadata, top-tags, duplicates, unresolved
