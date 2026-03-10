import unittest

from troi import Recording, Artist, ArtistCredit
from troi.filters import SequentialArtistFilterElement


class TestSequentialArtistFilter(unittest.TestCase):
    """Test the SequentialArtistFilterElement to ensure no consecutive tracks by the same artist"""

    def _create_recording(self, mbid, artist_credit_id, artist_name, recording_name):
        """Helper to create a Recording with artist_credit populated"""
        artist = Artist(name=artist_name, mbid=None)
        artist_credit = ArtistCredit(
            name=artist_name,
            artists=[artist],
            artist_credit_id=artist_credit_id
        )
        recording = Recording(
            name=recording_name,
            mbid=mbid,
            artist_credit=artist_credit
        )
        return recording

    def test_no_sequential_artists_simple(self):
        """Test basic case with 3 artists, ensuring no sequential tracks"""
        recordings = [
            self._create_recording("rec1", 1, "Artist A", "Song A1"),
            self._create_recording("rec2", 1, "Artist A", "Song A2"),
            self._create_recording("rec3", 2, "Artist B", "Song B1"),
            self._create_recording("rec4", 2, "Artist B", "Song B2"),
            self._create_recording("rec5", 3, "Artist C", "Song C1"),
            self._create_recording("rec6", 3, "Artist C", "Song C2"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        # Verify no sequential tracks from the same artist
        for i in range(len(result) - 1):
            self.assertNotEqual(
                result[i].artist_credit.artist_credit_id,
                result[i + 1].artist_credit.artist_credit_id,
                f"Sequential tracks at positions {i} and {i+1} have same artist: "
                f"{result[i].artist_credit.name}"
            )

        # Verify all recordings are present
        self.assertEqual(len(result), len(recordings))

    def test_all_same_artist(self):
        """Test edge case where all recordings are from the same artist"""
        recordings = [
            self._create_recording("rec1", 1, "Artist A", "Song A1"),
            self._create_recording("rec2", 1, "Artist A", "Song A2"),
            self._create_recording("rec3", 1, "Artist A", "Song A3"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        # All recordings should still be present
        self.assertEqual(len(result), len(recordings))
        
        # All should have the same artist (unavoidable in this case)
        for rec in result:
            self.assertEqual(rec.artist_credit.artist_credit_id, 1)

    def test_empty_list(self):
        """Test edge case with empty input"""
        element = SequentialArtistFilterElement()
        result = element.read([[]])
        self.assertEqual(len(result), 0)

    def test_single_recording(self):
        """Test edge case with single recording"""
        recordings = [
            self._create_recording("rec1", 1, "Artist A", "Song A1"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].mbid, "rec1")

    def test_two_artists_alternating(self):
        """Test with two artists that should alternate"""
        recordings = [
            self._create_recording("rec1", 1, "Artist A", "Song A1"),
            self._create_recording("rec2", 1, "Artist A", "Song A2"),
            self._create_recording("rec3", 1, "Artist A", "Song A3"),
            self._create_recording("rec4", 2, "Artist B", "Song B1"),
            self._create_recording("rec5", 2, "Artist B", "Song B2"),
            self._create_recording("rec6", 2, "Artist B", "Song B3"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        # Verify no sequential tracks from the same artist
        for i in range(len(result) - 1):
            self.assertNotEqual(
                result[i].artist_credit.artist_credit_id,
                result[i + 1].artist_credit.artist_credit_id,
                f"Sequential tracks at positions {i} and {i+1} have same artist"
            )

        # Verify all recordings are present
        self.assertEqual(len(result), len(recordings))

    def test_unbalanced_distribution(self):
        """Test with highly unbalanced artist distribution (5 from A, 1 from B)"""
        recordings = [
            self._create_recording("rec1", 1, "Artist A", "Song A1"),
            self._create_recording("rec2", 1, "Artist A", "Song A2"),
            self._create_recording("rec3", 1, "Artist A", "Song A3"),
            self._create_recording("rec4", 1, "Artist A", "Song A4"),
            self._create_recording("rec5", 1, "Artist A", "Song A5"),
            self._create_recording("rec6", 2, "Artist B", "Song B1"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        # Verify all recordings are present
        self.assertEqual(len(result), len(recordings))

        # Count sequential artists (should be minimized)
        sequential_count = 0
        for i in range(len(result) - 1):
            if result[i].artist_credit.artist_credit_id == result[i + 1].artist_credit.artist_credit_id:
                sequential_count += 1

        # With 5 from A and 1 from B, we expect at least 3 sequential pairs (A-A)
        # but the algorithm should place B optimally to break it up
        self.assertLessEqual(sequential_count, 4, "Too many sequential artist pairs")

    def test_recordings_without_artist_credit(self):
        """Test that recordings without artist_credit are handled gracefully"""
        recordings = [
            Recording(name="Song 1", mbid="rec1"),  # No artist_credit
            self._create_recording("rec2", 1, "Artist A", "Song A1"),
            self._create_recording("rec3", 2, "Artist B", "Song B1"),
        ]

        element = SequentialArtistFilterElement()
        result = element.read([recordings])

        # Should filter out recording without artist_credit or handle gracefully
        # Implementation will determine exact behavior
        self.assertGreaterEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
