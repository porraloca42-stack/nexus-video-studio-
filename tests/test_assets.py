import unittest
from unittest.mock import call, patch

from nexus.assets import rank_video_candidates, search_video_sources, diverse_candidate_shortlist


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
    def test_scene_query_results_reach_visual_review_even_when_metadata_uses_different_words(self, search):
        search.return_value = [
            clip("https://example.test/candidate.mp4", "Crowd beneath giant hand", "Concert crowd")
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
        )

        self.assertFalse(errors)
        self.assertEqual([item["url"] for item in ranked], ["https://example.test/candidate.mp4"])
        self.assertTrue(ranked[0]["matched_scene_query"])


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
    def test_style_only_result_without_scene_metadata_is_rejected(self, search):
        search.side_effect = [
            [],
            [],
            [clip("https://example.test/anime.mp4", "Anime fantasy landscape", "Japanese animation")],
        ]

        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
            style_query="anime fantasy landscape",
        )

        self.assertFalse(errors)
        self.assertEqual(ranked, [])

    def test_style_match_is_secondary_to_scene_semantics(self):
        candidates = [
            {
                **clip("https://example.test/semantic.mp4", "Person writing goals in notebook", "Writing in a journal"),
                "source": "Pixabay",
            },
            {
                **clip("https://example.test/style-only.mp4", "Anime fantasy landscape", "Japanese anime scenery"),
                "source": "Pexels",
            },
        ]
        ranked = rank_video_candidates(
            candidates,
            "person writing goals in notebook",
            style_query="anime 2D Japanese animation",
        )
        self.assertEqual(ranked[0]["url"], "https://example.test/semantic.mp4")
        self.assertGreater(ranked[0]["_nexus_relevance"], ranked[1]["_nexus_relevance"])

    @patch("nexus.assets.search_coverr_videos")
    def test_style_query_is_searched_separately_but_does_not_admit_style_only_results(self, search):
        search.side_effect = [
            [clip("https://example.test/semantic.mp4", "Person writing goals in notebook", "Writing in journal")],
            [],
            [clip("https://example.test/anime-only.mp4", "Anime landscape", "Japanese animation scenery")],
        ]
        ranked, errors = search_video_sources(
            "person writing goals in notebook",
            coverr_key="test-key",
            relevance_query="person writing goals in notebook",
            style_query="anime 2D animation",
        )
        self.assertFalse(errors)
        self.assertEqual([item["url"] for item in ranked], ["https://example.test/semantic.mp4"])
        self.assertEqual(search.call_count, 3)
        self.assertEqual(search.call_args_list[-1].args[0], "anime 2D animation")

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


    @patch("nexus.assets.requests.get")
    def test_pexels_adapter_parses_portrait_mp4_and_attribution(self, get):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "videos": [{
                        "url": "https://www.pexels.com/video/123/",
                        "alt": "A person writing in a notebook",
                        "user": {
                            "name": "Creator",
                            "url": "https://www.pexels.com/@creator/",
                        },
                        "video_files": [
                            {
                                "link": "https://videos.pexels.com/example.mp4",
                                "file_type": "video/mp4",
                                "quality": "hd",
                                "width": 1080,
                                "height": 1920,
                            }
                        ],
                    }]
                }

        get.return_value = FakeResponse()
        from nexus.assets import search_pexels_videos

        results = search_pexels_videos("person writing notebook", "secret", per_page=12)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["vertical"])
        self.assertEqual(results[0]["source"], "Pexels")
        self.assertEqual(results[0]["author"], "Creator")
        self.assertEqual(results[0]["source_url"], "https://www.pexels.com/video/123/")
        self.assertEqual(get.call_args.args[0], "https://api.pexels.com/v1/videos/search")
        self.assertEqual(get.call_args.kwargs["params"]["orientation"], "portrait")
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "secret")

    @patch("nexus.assets.search_pixabay_videos")
    @patch("nexus.assets.search_coverr_videos")
    def test_duplicate_asset_url_is_downloaded_once(self, coverr, pixabay):
        shared = "https://example.test/shared.mp4"
        coverr.return_value = [
            clip(shared, "Person walking through a city", "Urban street")
        ]
        pixabay.return_value = [
            clip(shared, "Person walking through a city", "Urban street")
        ]

        ranked, errors = search_video_sources(
            "person walking through a city",
            coverr_key="coverr-key",
            pixabay_key="pixabay-key",
        )

        self.assertFalse(errors)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["url"], shared)
        self.assertEqual(set(ranked[0]["also_found_by"]), {"Coverr", "Pixabay"})

    def test_shortlist_compares_distinct_libraries_before_repeating_one(self):
        candidates = [
            {**clip("https://example.test/pixabay1.mp4", "Person writing goals in notebook"), "source": "Pixabay", "_nexus_relevance": 9},
            {**clip("https://example.test/pixabay2.mp4", "Person writing journal at desk"), "source": "Pixabay", "_nexus_relevance": 8},
            {**clip("https://example.test/pexels.mp4", "Person writing goals in notebook"), "source": "Pexels", "_nexus_relevance": 7},
            {**clip("https://example.test/coverr.mp4", "Person writing goals in notebook"), "source": "Coverr", "_nexus_relevance": 6},
        ]
        shortlist = diverse_candidate_shortlist(candidates, limit=3)
        self.assertEqual([item["source"] for item in shortlist], ["Pixabay", "Pexels", "Coverr"])

    def test_shortlist_compares_distinct_libraries_before_repeating_one(self):
        candidates = [
            {**clip("https://example.test/pixabay1.mp4", "Person writing goals in notebook"), "source": "Pixabay", "_nexus_relevance": 9},
            {**clip("https://example.test/pixabay2.mp4", "Person writing journal at desk"), "source": "Pixabay", "_nexus_relevance": 8},
            {**clip("https://example.test/pexels.mp4", "Person writing goals in notebook"), "source": "Pexels", "_nexus_relevance": 7},
            {**clip("https://example.test/coverr.mp4", "Person writing goals in notebook"), "source": "Coverr", "_nexus_relevance": 6},
        ]
        shortlist = diverse_candidate_shortlist(candidates, limit=3)
        self.assertEqual([item["source"] for item in shortlist], ["Pixabay", "Pexels", "Coverr"])


if __name__ == "__main__":
    unittest.main()
