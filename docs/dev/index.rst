Developer Documentation
=======================

The documentation in this section describes the internal workings of Troi. Developers wishing
to use Troi shouldn't need to know about these modules, but if you wish to extend the
core functionality of Troi, this documentation is for you!

Note: There are some modules in troi directory that are not covered here -- those are important
for end users, so thos are defined in the main section of our docs.


troi.cli
--------

This module is the entry point for the troi command line interface. 

.. click:: troi.cli:cli
   :prog: python -m troi.cli
   :nested: short

troi.core
---------

Troi core module that creates and executes the patches:

.. automodule:: troi.core
    :members:

troi.patch
----------

Troi patch class definition:

.. automodule:: troi.patch
    :members:

troi.playlist
-------------

Troi playlist class that creates and serializes playlists:

.. automodule:: troi.playlist
    :members:

troi.print_recording
--------------------

Debugging module for printing out the information associated with recordings:

.. automodule:: troi.print_recording
    :members:

troi.utils
----------

Misc functions needed to run troi:

.. automodule:: troi.utils
    :members:
