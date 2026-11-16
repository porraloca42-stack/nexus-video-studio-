import unittest
from unittest.mock import patch

from nexus.assets import rank_video_candidates, search_video_sources


class AssetRankingTests(unittest.TestCase):
    def test_scene_relevance_beats_resolution(self):
        candidates = [
            {
                "url": "https://example.test/unrelated.mp4",
                "title": "Crowd beneath giant hand",
                "description": "Large crowd at a concert",
                "vertical": True,
                "width": 1080,
                "height": 1920,
            },
            {
                "url": "https://example.test/relevant.mp4",
                "title": "Person writing goals in notebook",
                "description": "Close up of hand writing in a journal",
                "vertical": False,
                "width": 3840,
                "height": 2160,
            },
        ]

        ranked = rank_video_candidates(candidates, "person writing goals in notebook")

        self.assertEqual(ranked[0]["url"], "https://example.test/relevant.mp4")

    @patch("nexus.assets.search_coverr_videos")
    def test_excludes_clips_already_used_in_previous_scenes(self, search):
        search.return_value = [
            {
                "url": "https://example.test/used.mp4",
                "title": "Person writing goals in notebook",
                "description": "Writing in a journal",
                "vertical": True,
                "width": 1080,
                "height": 1920,
            },
            {
                "url": "https://example.test/new.mp4",
                "title": "Writing goals in a notebook close up",
                "description": "Hand writing in journal",
                "vertical": True,
                "width": 1080,
                "height": 1920,
            },
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
            exclude_urls={"https://example.test/used.mp4"},
        )

        self.assertFalse(errors)
        self.assertEqual([item["url"] for item in ranked], ["https://example.test/new.mp4"])

    def test_empty_results_are_safe(self):
        self.assertEqual(rank_video_candidates([], "a scene query"), [])


if __name__ == "__main__":
    unittest.main()
