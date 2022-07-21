import json
import unittest
import unittest.mock

import troi
import troi.listenbrainz.similar_users

return_json = { "payload" : [
    {
        "similarity": 1,
        "user_name": "Damselfish"
    },
    {
        "similarity": 0.5906434294705439,
        "user_name": "throwawaytest140"
    },
    {
        "similarity": 0.4343819478596525,
        "user_name": "Delphik"
    }
]}


class TestSimilarUserLookup(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        user_name = "butthead"

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.json = unittest.mock.MagicMock(return_value=return_json)
        req.return_value = mock
        e = troi.listenbrainz.similar_users.SimilarUserLookupElement(user_name)

        entities = e.read([])
        req.assert_called_with(e.SERVER_URL % user_name)

        assert len(entities) == 3
        assert entities[0]['similarity'] == 1.0
        assert entities[0]['user_name'] == 'Damselfish'
        assert entities[1]['similarity'] == 0.5906434294705439
        assert entities[1]['user_name'] == 'throwawaytest140'
        assert entities[2]['similarity'] ==0.4343819478596525 
        assert entities[2]['user_name'] == 'Delphik'
