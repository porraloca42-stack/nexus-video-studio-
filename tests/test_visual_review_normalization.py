import pytest

from nexus.visual_review import normalize_review


def test_normalize_review_clamps_scores_and_marks_missing_scenes():
    scenes = [{"voiceover": "Uma pessoa abre a janela."}, {"voiceover": "A luz entra."}]
    result = normalize_review({"reviews": [
        {"scene_number": 1, "semantic_score": 14, "matches_narration": True,
         "visual_quality": "Boa composição", "issues": [], "recommendation": "Manter"},
        {"scene_number": 99, "semantic_score": 8},
    ]}, scenes)
    assert result[0]["semantic_score"] == 10
    assert result[0]["matches_narration"] is True
    assert result[1]["issues"] == ["missing_review"]


def test_normalize_review_rejects_missing_reviews():
    with pytest.raises(ValueError):
        normalize_review({}, [{"voiceover": "fala"}])
