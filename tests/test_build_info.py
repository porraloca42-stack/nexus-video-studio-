import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.build_info import get_runtime_build_info


class RuntimeBuildInfoTests(unittest.TestCase):
    def test_reads_checked_out_commit_sha(self):
        completed = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--verify", "HEAD"],
            returncode=0,
            stdout="ABCDEF0123456789abcdef0123456789abcdef01\n",
            stderr="",
        )
        with patch("nexus.build_info.subprocess.run", return_value=completed) as run:
            sha, source = get_runtime_build_info(Path("/app"), environ={})

        self.assertEqual(sha, "abcdef0123456789abcdef0123456789abcdef01")
        self.assertEqual(source, "git")
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["git", "rev-parse", "--verify", "HEAD"])
        self.assertEqual(run.call_args.kwargs["cwd"], "/app")

    def test_uses_deployment_sha_when_git_metadata_is_unavailable(self):
        completed = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--verify", "HEAD"],
            returncode=128,
            stdout="",
            stderr="not a git repository",
        )
        with patch("nexus.build_info.subprocess.run", return_value=completed):
            sha, source = get_runtime_build_info(
                Path("/app"), environ={"STREAMLIT_GIT_SHA": "1234567890abcdef"}
            )

        self.assertEqual(sha, "1234567890abcdef")
        self.assertEqual(source, "STREAMLIT_GIT_SHA")

    def test_rejects_invalid_environment_sha(self):
        completed = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--verify", "HEAD"],
            returncode=128,
            stdout="",
            stderr="not a git repository",
        )
        with patch("nexus.build_info.subprocess.run", return_value=completed):
            sha, source = get_runtime_build_info(
                Path("/app"),
                environ={"STREAMLIT_GIT_SHA": "main", "GITHUB_SHA": "not-a-sha"},
            )

        self.assertIsNone(sha)
        self.assertIsNone(source)

    def test_falls_back_when_git_command_cannot_run(self):
        with patch(
            "nexus.build_info.subprocess.run",
            side_effect=FileNotFoundError("git unavailable"),
        ):
            sha, source = get_runtime_build_info(
                Path("/app"), environ={"GITHUB_SHA": "fedcba9876543210"}
            )

        self.assertEqual(sha, "fedcba9876543210")
        self.assertEqual(source, "GITHUB_SHA")


if __name__ == "__main__":
    unittest.main()
