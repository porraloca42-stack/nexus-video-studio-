import unittest

from nexus.hf_cache import download_with_cache_metrics


class LocalEntryNotFoundError(Exception):
    pass


class HuggingFaceCacheMetricsTests(unittest.TestCase):
    def test_cache_hit_avoids_remote_download(self):
        calls = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            self.assertTrue(kwargs["local_files_only"])
            return "/models/cached.safetensors"

        result = download_with_cache_metrics(
            fake_download,
            LocalEntryNotFoundError,
            repo_id="example/model",
            filename="cached.safetensors",
            cache_dir="/models",
        )

        self.assertEqual(result["path"], "/models/cached.safetensors")
        self.assertTrue(result["cache_hit"])
        self.assertEqual(result["download_seconds"], 0.0)
        self.assertEqual(len(calls), 1)

    def test_cache_miss_downloads_once_and_reports_miss(self):
        calls = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            if kwargs.get("local_files_only"):
                raise LocalEntryNotFoundError("not cached")
            return "/models/downloaded.safetensors"

        result = download_with_cache_metrics(
            fake_download,
            LocalEntryNotFoundError,
            repo_id="example/model",
            filename="downloaded.safetensors",
            cache_dir="/models",
        )

        self.assertEqual(result["path"], "/models/downloaded.safetensors")
        self.assertFalse(result["cache_hit"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0]["local_files_only"])
        self.assertNotIn("local_files_only", calls[1])

    def test_non_cache_errors_propagate_without_retry(self):
        calls = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            raise PermissionError("authentication failed")

        with self.assertRaisesRegex(PermissionError, "authentication failed"):
            download_with_cache_metrics(
                fake_download,
                LocalEntryNotFoundError,
                repo_id="private/model",
                filename="weights.safetensors",
                cache_dir="/models",
            )

        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
