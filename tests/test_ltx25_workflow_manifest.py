import json
import unittest
from pathlib import Path


class LTX25WorkflowManifestTests(unittest.TestCase):
    def test_upstream_workflow_is_pinned_and_not_misrepresented_as_api_prompt(self):
        path = Path(__file__).resolve().parents[1] / "workflows" / "ltx25" / "source_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["engine"], "ltx25_comfyui")
        self.assertEqual(
            manifest["upstream"]["commit"],
            "db476dacc1469b2f17ccc5735693916afcb6fac1",
        )
        self.assertEqual(manifest["source_format"], "comfyui_visual_workflow")
        self.assertFalse(manifest["api_prompt_exported"])
        self.assertFalse(manifest["status"]["worker_integrated"])

    def test_manifest_records_nested_workflow_groups_and_nexus_constraints(self):
        path = Path(__file__).resolve().parents[1] / "workflows" / "ltx25" / "source_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))

        groups = {item["name"]: item for item in manifest["graph"]["subgraphs"]}
        self.assertEqual(len(groups), 6)
        self.assertIn("Upscale and re-sampler (3 steps)", groups)
        self.assertEqual(manifest["graph"]["frame_count_constraint"], "1 + 8n")
        self.assertEqual(manifest["nexus_adaptation"]["target_aspect_ratio"], "9:16")
        self.assertTrue(manifest["nexus_adaptation"]["discard_generated_ltx_audio"])
        self.assertEqual(manifest["nexus_adaptation"]["final_composition"], "Remotion")


if __name__ == "__main__":
    unittest.main()
