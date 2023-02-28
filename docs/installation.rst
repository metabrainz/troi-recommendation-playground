.. _installation:

Installation
============

Installation for End Users
--------------------------

At this point in time we're not quite ready for end users to install Troi. However, for developers, follow the instructions
below.

Installation for Development
----------------------------

Linux and Mac
^^^^^^^^^^^^^

Use these command line arguments to install Troi on Linux and Mac:

.. code-block:: bash

    virtualenv -p python3 .ve
    source .ve/bin/activate
    pip3 install -r requirements.txt -r requirements_test.txt
    python3 -m troi.cli --help

Windows
^^^^^^^

Use these commands to install on Windows:

.. code-block:: bash

    virtualenv -p python .ve
    .ve\Scripts\activate.bat
    pip install -r requirements.txt -r requirements_test.txt
    python -m troi.cli --help

