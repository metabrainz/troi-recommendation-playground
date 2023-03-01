Elements
========

troi.filters
------------

Elements that are used as filter to remove some parts of the data passed into it:

.. autoclass:: troi.filters.ArtistCreditFilterElement
.. autoclass:: troi.filters.ArtistCreditLimiterElement
.. autoclass:: troi.filters.DuplicateRecordingMBIDFilterElement
.. autoclass:: troi.filters.DuplicateRecordingArtistCreditFilterElement
.. autoclass:: troi.filters.ConsecutiveRecordingFilterElement
.. autoclass:: troi.filters.EmptyRecordingFilterElement
.. autoclass:: troi.filters.YearRangeFilterElement
.. autoclass:: troi.filters.GenreFilterElement
.. autoclass:: troi.filters.LatestListenedAtFilterElement
.. autoclass:: troi.filters.HatedRecordingsFilterElement


troi.loops
----------

Elements useful for runnning Troi for many users:

.. autoclass:: troi.loops.ForLoopElement


troi.operations
---------------

Elements that perform operations on the data pipeline, such as union, difference, intersection and uniqing.

.. autoclass:: troi.operations.UniqueElement
.. autoclass:: troi.operations.UnionElement
.. autoclass:: troi.operations.IntersectionElement
.. autoclass:: troi.operations.DifferenceElement
.. autoclass:: troi.operations.ZipperElement


troi.sorts
----------

Elements that sort the data in a pipeline:

.. autoclass:: troi.sorts.YearSortElement
