import unittest

from nexus.captions import (
    build_alignment_caption_events,
    captions_cover_word_alignment,
)


class AlignmentCaptionTests(unittest.TestCase):
    def test_groups_verified_words_into_short_cues_and_preserves_source_times(self):
        words = [
            {"text": "Esse", "start_seconds": 0.0, "end_seconds": 0.2},
            {"text": "segredo", "start_seconds": 0.21, "end_seconds": 0.55},
            {"text": "muda", "start_seconds": 0.56, "end_seconds": 0.8},
            {"text": "tudo.", "start_seconds": 0.81, "end_seconds": 1.15},
            {"text": "Olha", "start_seconds": 1.3, "end_seconds": 1.55},
            {"text": "isso!", "start_seconds": 1.56, "end_seconds": 1.9},
        ]

        result = build_alignment_caption_events(words, 2.0)

        self.assertEqual(result["alignment_level"], "word")
        self.assertEqual([event["text"] for event in result["events"]], [
            "Esse segredo muda tudo.", "Olha isso!",
        ])
        self.assertEqual(result["events"][0]["start_seconds"], 0.0)
        self.assertEqual(result["events"][0]["end_seconds"], 1.15)
        self.assertEqual(
            [word["start_seconds"] for event in result["events"] for word in event["words"]],
            [item["start_seconds"] for item in words],
        )
        self.assertTrue(captions_cover_word_alignment(result["events"], words))

    def test_splits_word_cues_by_readability_without_inventing_timestamps(self):
        words = [
            {"text": "Uma", "start_seconds": 0.0, "end_seconds": 0.2},
            {"text": "frase", "start_seconds": 0.2, "end_seconds": 0.45},
            {"text": "curta", "start_seconds": 0.45, "end_seconds": 0.7},
            {"text": "que", "start_seconds": 0.7, "end_seconds": 0.82},
            {"text": "continua", "start_seconds": 0.82, "end_seconds": 1.15},
            {"text": "agora", "start_seconds": 1.15, "end_seconds": 1.45},
        ]

        result = build_alignment_caption_events(words, 1.5, max_words=3)

        self.assertEqual([event["text"] for event in result["events"]], [
            "Uma frase curta", "que continua agora",
        ])
        self.assertEqual(result["events"][1]["start_seconds"], 0.7)
        self.assertEqual(result["events"][1]["end_seconds"], 1.45)

    def test_phrase_alignment_uses_exact_phrase_intervals_without_word_highlights(self):
        segments = [
            {"text": "A ideia principal", "start_seconds": 0.1, "end_seconds": 0.9},
            {"text": "vem depois.", "start_seconds": 1.0, "end_seconds": 1.6},
        ]

        result = build_alignment_caption_events(segments, 1.8)

        self.assertEqual(result["alignment_level"], "phrase")
        self.assertEqual([event["text"] for event in result["events"]], [
            "A ideia principal", "vem depois.",
        ])
        self.assertEqual(result["events"][0]["start_seconds"], 0.1)
        self.assertEqual(result["events"][0]["end_seconds"], 0.9)
        self.assertEqual(result["events"][0]["words"], [])
        self.assertIn("sem destaque palavra a palavra", result["warning"])

    def test_omits_overlong_phrase_instead_of_fabricating_word_timing(self):
        result = build_alignment_caption_events(
            [{"text": "esta frase alinhada é longa demais para uma legenda vertical confortável",
              "start_seconds": 0.0, "end_seconds": 2.0}],
            2.0,
        )

        self.assertEqual(result["events"], [])
        self.assertEqual(result["alignment_level"], "unavailable")
        self.assertIn("foi omitido", result["warning"])

    def test_rejects_bad_or_out_of_range_alignment(self):
        result = build_alignment_caption_events(
            [{"text": "fora", "start_seconds": 0.0, "end_seconds": 2.1}],
            2.0,
        )

        self.assertEqual(result["events"], [])
        self.assertEqual(result["alignment_level"], "unavailable")
        self.assertIn("inválidos", result["warning"])

    def test_rejects_incomplete_brain4_caption_coverage(self):
        expected = [
            {"text": "A", "start_seconds": 0.0, "end_seconds": 0.2},
            {"text": "verdade.", "start_seconds": 0.2, "end_seconds": 0.7},
        ]
        incomplete = [{
            "words": [{"text": "A", "start_seconds": 0.0, "end_seconds": 0.2}],
        }]
        self.assertFalse(captions_cover_word_alignment(incomplete, expected))


if __name__ == "__main__":
    unittest.main()
