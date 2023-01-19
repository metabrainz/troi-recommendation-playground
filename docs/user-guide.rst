.. _user-guide:

User Guide
==========

Once you have installed Troi, get familiar with how the command line works. To get the usage for Troi, do this:

.. code-block:: bash

   python -m troi.cli


To list all the patches that are currently available, do:

.. code-block:: bash

   python -m troi.cli list


To generate a playlist from a patch and display it in the terminal, do:

.. code-block:: bash

   python -m troi.cli playlist --print daily-jams <user_name>

This will generate a playlist and print the list to the terminal.


To generate a playlist from a patch and display it and then upload it to ListenBrainz:

.. code-block:: bash

   python -m troi.cli playlist --print --upload --token <user-token> daily-jams <user_name>

This will generate a playlist and print the list to the terminal and then upload it to ListenBrainz. You can find your
user token on your `profile page at ListenBrainz <https://listenbrainz.org/profile/>`_.

From here on you can explore different :ref:`patches` or read how Troi works :ref:`technical-introduction`
