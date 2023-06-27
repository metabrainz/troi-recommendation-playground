Troi Recommendation Toolkit
===========================

This project aims to create an open source music recommendation toolkit with an API-first
philiosophy. API-first means that user do no need to download a lot of data before they
can start working with Troi -- all the needed data should ideally live in online APIs, making
it very easy for someone to get started hacking on music recommendations.

Troi implements a toolkit that allows developers to create data pipelines comprised of Elements
that generate, filter or manipulate data in a data pipeline. Troi assumes that MusicBrainz IDs
are available for all the data passing through the system. This allows us to create a powerful
toolkit underpinned by rich datasets, but it does have the disadvantage that recommendations
can only be created for music present in MusicBrainz.

For a much more detailed introduction to Troi, please see :ref:`technical-introduction`.

User Guide
----------

For end-user guide on how to run Troi and what the various command line arguments are, please
see our :ref:`user-guide`.


MetaBrainz APIs
---------------

To accomplish the goal of an API-first toolkit, we, have created and hosted a number of data-sets
that can be accessed as a part of this project. From Troi you can call any API you'd like, including
the MusicBrainz and ListenBrainz APIs. We have also created the following sites with more API endpoints
to support Troi:

#. More stable APIs are hosted on our `Labs API page <https://labs.api.listenbrainz.org>`_. We work hard to ensure that these APIs stay up at all times, but we do not guarantee it. Best to not use for production.
#. More transient APIs that we do not guarantee to always be up can be found on our `data sets page <https://datasets.listenbrainz.org>`_. Do not use for production!

The ListenBrainz project offers a number of data sets:

#. Collaborative filtered recordings that suggest what recordings a user should listen to based on their previous listening habits. See the `recommended tracks for user rob <https://listenbrainz.org/recommended/tracks/rob/?page=1>`_.
#. User statistics that were derived from users recent `listening habits <https://listenbrainz.readthedocs.io/en/latest/users/api/statistics.html>`_.

We will continue to build and host more datasets as time passes. If an API endpoint becomes useful to
a greater number of people we will elevate these API endpoints to officially supported endpoints
that we ensure are up to date on online at all times.

Trivia
------

The project is named after `Deanna Troi <https://en.wikipedia.org/wiki/Deanna_Troi>`_, the empath on the
TV series Star Trek: The Next Generation.

.. toctree::
   :maxdepth: 2
   :caption: Troi Documentation Index

   installation.rst
   user-guide.rst
   introduction.rst
   patches
   entities
   elements/index
   elements/musicbrainz
   elements/listenbrainz
   lb_radio.rst
   dev/index


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
