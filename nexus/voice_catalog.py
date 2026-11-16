"""User-curated narration voice IDs and conservative metadata classification.

The provider labels and model IDs below were supplied by the NEXUS owner.
Gender is inferred only from explicit model metadata; otherwise it stays unknown.
"""
import re
import unicodedata


CURATED_VOICE_GROUPS = {
    "CapCut": [
        "288c050d6afc4a088d085847f941c819",
        "637752e9b9bf4c3981c73b3d2b8df641",
        "c270179948cd44ddbe0d3975ebfe9eae",
        "d38abd6279444524a74e7d3e967bf626",
        "31d0bd6f6d774a92af605811b46a949a",
        "bef192f0b6964890904c994ca04a02f4",
        "2624ae1c840148a8a503a3cf62a68f99",
        "cd236d503031478fa939a6cd1ba43706",
        "a396c49439a94799987af30751bda108",
        "5d61225ce57f4134adc5b4a56adfa6df",
        "5073d6779ab8473e9ebd818962c6bd14",
        "0f69fe13eb254f1381ed28bc5231a62e",
        "bf7d34b3a9f646b19bc956b0dab0e156",
        "dd7f1ca877f14eff8e0564bf81b354e0",
    ],
    "ElevenLabs": [
        "a8be0b8358514f6e8d5b15c2731d6b96",
        "ed4a509ddec942369ec132b3eb1bafb1",
        "2cec6514953346978c0a7f4e78f9b423",
        "95204385531e4768b5ea6e2b4c6e8dda",
    ],
    "Licenciadas Fish": [
        "0ffee1af32254090b3630823baade12b",
        "add7bcb8d3c8423bbfa152ca232aad6e",
        "b3c060cc41544a7da94a2c487647c902",
        "70d10a6856b241ca81e5abe3bc0ec3e8",
        "9199d0840c7b4247b9d151b0cdd1d819",
        "fa56d74109154b3ea71e48bea2571107",
        "49762ba76fc1493985a3d48bf9a27ea4",
        "1c122e97870b4e60b63f2c3f68c11bd6",
        "507340ddfb8b4cc4946802d649c9f8fe",
        "2c21901cf2a542c389039307c33a9c9a",
        "8a7ccb95aab74376869ddcc01272e6a9",
        "3b159f0b046c443da15eb1516fdd38a3",
        "63d80e94864248d19f5b18d032982ea6",
        "68fdb8cb667d4668809dcc9e471b18ae",
        "ebcee40b10fb4a0fa484f0747d2c0090",
        "9f70893295924807b5bf64f32daac97d",
        "d1e5eb65a22e49529c352aacd31fd2b7",
        "1c58a6d68557461fa5687843ccc6390f",
        "0b12d715e4c741399594fccb12d4bbe2",
        "0ba1afd27db44eb2b4cb27fd331b93aa",
        "4d72497e3ceb4c75a7c5563900975afd",
        "a0a26a57cac94ea4918f05a2393b4259",
    ],
}


def curated_voice_entries():
    """Return a fresh flat list while preserving the user's provider grouping/order."""
    return [
        {"id": voice_id, "category": category}
        for category, voice_ids in CURATED_VOICE_GROUPS.items()
        for voice_id in voice_ids
    ]


def infer_voice_gender(metadata):
    """Infer gender only when model metadata explicitly identifies one."""
    metadata = metadata if isinstance(metadata, dict) else {}
    explicit = metadata.get("gender") or metadata.get("voice_gender") or metadata.get("sex")
    values = [str(explicit)] if explicit else []
    for key in ("title", "description", "tags", "gender_tags"):
        value = metadata.get(key) or []
        if isinstance(value, (list, tuple, set)):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))

    normalized = unicodedata.normalize("NFKD", " ".join(values).casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    words = set(re.findall(r"[a-z]+", normalized))
    male = bool(words.intersection({"male", "masculine", "masculino", "homem", "man", "boy"}))
    female = bool(words.intersection({"female", "feminine", "feminino", "mulher", "woman", "girl"}))
    if male == female:
        return "unknown"
    return "male" if male else "female"
