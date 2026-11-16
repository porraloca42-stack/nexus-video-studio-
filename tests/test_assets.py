import unittest
from unittest.mock import call, patch

from nexus.assets import rank_video_candidates, search_video_sources


def clip(url, title, description="", vertical=True, width=1080, height=1920):
    return {
        "url": url,
        "title": title,
        "description": description,
        "vertical": vertical,
        "width": width,
        "height": height,
    }


class AssetRankingTests(unittest.TestCase):
    def test_scene_relevance_beats_resolution(self):
        candidates = [
            clip(
                "https://example.test/unrelated.mp4",
                "Crowd beneath giant hand",
                "Large crowd at a concert",
                vertical=True,
                width=1080,
                height=1920,
            ),
            clip(
                "https://example.test/relevant.mp4",
                "Person writing goals in notebook",
                "Close up of hand writing in a journal",
                vertical=False,
                width=3840,
                height=2160,
            ),
        ]

        ranked = rank_video_candidates(candidates, "person writing goals in notebook")

        self.assertEqual(ranked[0]["url"], "https://example.test/relevant.mp4")

    @patch("nexus.assets.search_coverr_videos")
    def test_unrelated_results_are_rejected_and_shorter_query_is_tried(self, search):
        search.side_effect = [
            [clip("https://example.test/unrelated.mp4", "Crowd beneath giant hand", "Concert crowd")],
            [clip("https://example.test/relevant.mp4", "Writing goals in notebook", "Hand writing in journal")],
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
            relevance_query="person writing goals in notebook",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked[0]["url"], "https://example.test/relevant.mp4")
        self.assertGreaterEqual(search.call_count, 2)

    @patch("nexus.assets.search_coverr_videos")
    def test_style_terms_do_not_replace_scene_semantics(self, search):
        search.return_value = [
            clip(
                "https://example.test/relevant.mp4",
                "Person writing goals in notebook",
                "Close up of writing in a journal",
            )
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook cinematic 35mm natural light",
            coverr_key="test-key",
            relevance_query="person writing goals in notebook",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked[0]["url"], "https://example.test/relevant.mp4")

    @patch("nexus.assets.search_coverr_videos")
    def test_excludes_clips_already_used_in_previous_scenes(self, search):
        search.return_value = [
            clip("https://example.test/used.mp4", "Person writing goals in notebook"),
            clip("https://example.test/new.mp4", "Writing goals in a notebook close up", "Hand writing in journal"),
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
            exclude_urls={"https://example.test/used.mp4"},
        )

        self.assertFalse(errors)
        self.assertEqual([item["url"] for item in ranked], ["https://example.test/new.mp4"])

    @patch("nexus.assets.search_coverr_videos")
    def test_all_unrelated_results_return_empty_instead_of_false_match(self, search):
        search.return_value = [
            clip("https://example.test/unrelated.mp4", "Crowd beneath giant hand", "Concert crowd")
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked, [])


    @patch("nexus.assets.search_coverr_videos")
    def test_single_scene_term_match_is_used_only_as_last_resort(self, search):
        search.return_value = [
            clip("https://example.test/weak.mp4", "Writing in a journal", "")
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
        )

        self.assertFalse(errors)
        self.assertEqual([item["url"] for item in ranked], ["https://example.test/weak.mp4"])

    @patch("nexus.assets.search_coverr_videos")
    def test_unrelated_stock_is_still_rejected_by_semantic_fallback(self, search):
        search.return_value = [
            clip("https://example.test/unrelated.mp4", "Crowd beneath giant hand", "Concert crowd")
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked, [])

    def test_empty_results_are_safe(self):
        self.assertEqual(rank_video_candidates([], "a scene query"), [])


    @patch("nexus.assets.search_pexels_videos")
    @patch("nexus.assets.search_pixabay_videos")
    @patch("nexus.assets.search_coverr_videos")
    def test_searches_every_enabled_provider_and_combines_candidates(self, coverr, pixabay, pexels):
        coverr.return_value = [
            clip("https://example.test/coverr.mp4", "Person walking through a city", "Urban street")
        ]
        pixabay.return_value = [
            clip("https://example.test/pixabay.mp4", "Person walking through city street", "Urban walk")
        ]
        pexels.return_value = [
            clip("https://example.test/pexels.mp4", "Person walking through a city", "Walking downtown")
        ]

        ranked, errors = search_video_sources(
            "person walking through a city",
            coverr_key="coverr-key",
            pixabay_key="pixabay-key",
            pexels_key="pexels-key",
        )

        self.assertFalse(errors)
        self.assertEqual({item["source"] for item in ranked}, {"Coverr", "Pixabay", "Pexels"})
        self.assertEqual(coverr.call_count, 2)
        self.assertEqual(pixabay.call_count, 2)
        self.assertEqual(pexels.call_count, 2)

    @patch("nexus.assets.search_pexels_videos")
    def test_pexels_adapter_uses_current_video_endpoint_and_normalizes_files(self, search):
        search.return_value = [
            clip("https://example.test/pexels.mp4", "Person writing in a journal", "Writing")
        ]

        ranked, errors = search_video_sources(
            "person writing in a journal",
            pexels_key="pexels-key",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked[0]["source"], "Pexels")
        self.assertEqual(search.call_count, 2)

    @patch("nexus.assets.search_pixabay_videos")
    @patch("nexus.assets.search_coverr_videos")
    def test_provider_failure_does_not_block_other_libraries(self, coverr, pixabay):
        coverr.side_effect = __import__("requests").RequestException("Coverr unavailable")
        pixabay.return_value = [
            clip("https://example.test/pixabay.mp4", "Person writing goals in notebook", "Journal writing")
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="coverr-key",
            pixabay_key="pixabay-key",
        )

        self.assertTrue(errors)
        self.assertEqual(ranked[0]["source"], "Pixabay")


if __name__ == "__main__":
    unittest.main()
