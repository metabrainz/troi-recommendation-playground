import json
import unittest
import unittest.mock

import troi
import troi.acousticbrainz.annoy
from troi import PipelineError

return_json = {
    "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf": {
        "0": [
                {
                    "distance": 0.00010826535435626283,
                    "offset": 0,
                    "recording_mbid": "7b3ecb51-919b-494d-8085-47e3390dd212"
                },
                {
                    "distance": 0.3184245228767395,
                    "offset": 0,
                    "recording_mbid": "724335d8-4ae6-4b2d-8be5-056944b8132d"
                },
                {
                    "distance": 0.3630277216434479,
                    "offset": 0,
                    "recording_mbid": "d4b46b96-ab56-4f99-a59e-bab590deed8f"
                },
                {
                    "distance": 0.3671037256717682,
                    "offset": 0,
                    "recording_mbid": "441a879f-4b8c-4d52-8a6f-e289bef2fd83"
                },
                {
                    "distance": 0.3676069676876068,
                    "offset": 0,
                    "recording_mbid": "b26b7d9f-dd39-4b74-89f0-a534d6bbf556"
                },
                {
                    "distance": 0.385963499546051,
                    "offset": 0,
                    "recording_mbid": "c1d750f3-93ea-4e0e-85f0-8baa8548c97a"
                },
            ]
    }
}


class TestAnnoyLookupElement(unittest.TestCase):

    @unittest.mock.patch('requests.get')
    def test_read(self, req):

        mock = unittest.mock.MagicMock()
        mock.status_code = 200
        mock.text = json.dumps(return_json)
        req.return_value = mock
        e = troi.acousticbrainz.annoy.AnnoyLookupElement("mfccs", "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf")

        entities = e.read([[]])
        req.assert_called_with(e.SERVER_URL + "mfccs", params={
            "remove_dups": "true", "recording_ids": ["8f8cc91f-0bca-4351-90d4-ef334ac0a0cf"]
        })

        assert len(entities) == 6
        assert entities[0].acousticbrainz == {
            "metric": "mfccs",
            "similarity_from": "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf",
            "similarity": 0.00010826535435626283,
            "offset": 0,
        }
        assert entities[0].mbid == "7b3ecb51-919b-494d-8085-47e3390dd212"

    def test_invalid_metric(self):
        with self.assertRaises(PipelineError):
            troi.acousticbrainz.annoy.AnnoyLookupElement("foo", "8f8cc91f-0bca-4351-90d4-ef334ac0a0cf")
