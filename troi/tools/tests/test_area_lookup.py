import json
import unittest
import unittest.mock

import troi
import troi.tools.area_lookup

request_json = [
    {
        "[area]": "Germany"
    }
]

return_json = [
    {
        "area_mbid": "85752fda-13c4-31a3-bee5-0e5cb1f51dad",
        "area_name": "Germany"
    }
]

class TestAreaLookup(unittest.TestCase):

    @unittest.mock.patch('requests.post')
    def test_area_lookup(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        area_id = troi.tools.area_lookup.area_lookup(request_json[0]["[area]"])
        req.assert_called_with(troi.tools.area_lookup.AREA_LOOKUP_SERVER_URL, json=request_json)

        assert area_id == "85752fda-13c4-31a3-bee5-0e5cb1f51dad"
