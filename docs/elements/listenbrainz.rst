ListenBrainz Elements
=====================

The following elements fetch data from ListenBrainz:

troi.listenbrainz.dataset_fetcher.DataSetFetcherElement
-------------------------------------------------------

ListenBrainz has developed a tool called the `dataset hoster <https://github.com/metabrainz/data-set-hoster>`_ which allows
us to quickly host SQL queries on the web. This Element is a shortcut for fetching data from one of these endpoints
and to return a list of Recordings.

.. autoclass:: troi.listenbrainz.dataset_fetcher.DataSetFetcherElement

troi.listenbrainz.feedback.ListensFeedbackLookup
------------------------------------------------

Given a list of Recordings as input, fetch the feedback (like/hate) for a given user_name.


.. autoclass:: troi.listenbrainz.feedback.ListensFeedbackLookup

troi.listenbrainz.listens.RecentListensTimestampLookup
-------------------------------------------------------

Given a list of Recordings, fetch the timestamp for when that Recording was listened to in the window specified by the days parameter.

.. autoclass:: troi.listenbrainz.listens.RecentListensTimestampLookup


troi.listenbrainz.recs.UserRecordingRecommendationsElement
----------------------------------------------------------

Given a user_name and artist_type, fetch Recordings for that user if they are available. artist_type must be one of
"top" for top artist recommendations (for that user), "similar" for similar artist recommendations (also for that user) or
"raw" recommendations that have not be filtered like the top/similar recommendations.

.. autoclass:: troi.listenbrainz.recs.UserRecordingRecommendationsElement


troi.listenbrainz.stats.UserArtistsElement
------------------------------------------

Given a user_name and a time_range, fetch the top artist statistics for that user and time_range. Available time_ranges are
defined `in the ListenBrainz Statistics API documentation <https://listenbrainz.readthedocs.io/en/latest/users/api/statistics.html#constants>`_.

.. autoclass:: troi.listenbrainz.stats.UserArtistsElement


troi.listenbrainz.stats.UserReleasesElement
-------------------------------------------

Given a user_name and a time_range, fetch the top release statistics for that user and time_range. Available time_ranges are
defined `in the ListenBrainz Statistics API documentation <https://listenbrainz.readthedocs.io/en/latest/users/api/statistics.html#constants>`_.

.. autoclass:: troi.listenbrainz.stats.UserReleasesElement

troi.listenbrainz.stats.UserRecordingsElement
---------------------------------------------

Given a user_name and a time_range, fetch the top recording statistics for that user and time_range. Available time_ranges are
defined `in the ListenBrainz Statistics API documentation <https://listenbrainz.readthedocs.io/en/latest/users/api/statistics.html#constants>`_.

.. autoclass:: troi.listenbrainz.stats.UserRecordingElement


troi.listenbrainz.user.UserListElement
--------------------------------------

Given a list of users, return those users as User objects.

.. autoclass:: troi.listenbrainz.user.UserListElement


troi.listenbrainz.yim_user.YIMUserListElement
---------------------------------------------

This Element is used for when we run the Year in Music report and create playlists. The elment fetches the list of
users who should have YIM playlists generated and returns them.

.. autoclass:: troi.listenbrainz.yim_user.YIMUserListElement
