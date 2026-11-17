import unittest

from nexus.gpu_identity import validate_gpu_identity


class GPUIdentityTests(unittest.TestCase):
    def test_accepts_matching_l40s_runtime(self):
        result = validate_gpu_identity("L40S", "NVIDIA L40S")
        self.assertTrue(result["gpu_identity_verified"])
        self.assertEqual(result["requested_gpu_type"], "L40S")
        self.assertEqual(result["actual_gpu_name"], "NVIDIA L40S")

    def test_rejects_h100_when_l40s_was_requested(self):
        with self.assertRaisesRegex(RuntimeError, "solicitou L40S.*reportou NVIDIA H100"):
            validate_gpu_identity("L40S", "NVIDIA H100 80GB HBM3")

    def test_rejects_missing_gpu_identity(self):
        with self.assertRaisesRegex(RuntimeError, "GPU real não identificada"):
            validate_gpu_identity("L40S", "unknown")

    def test_accepts_a10g_runtime(self):
        result = validate_gpu_identity("A10", "NVIDIA A10G")
        self.assertTrue(result["gpu_identity_verified"])

    def test_rejects_a100_when_a10_was_requested(self):
        with self.assertRaisesRegex(RuntimeError, "solicitou A10.*reportou NVIDIA A100"):
            validate_gpu_identity("A10", "NVIDIA A100 80GB")

    def test_rejects_unmapped_requested_gpu_type(self):
        with self.assertRaisesRegex(RuntimeError, "sem regra de validação"):
            validate_gpu_identity("GPU-UNKNOWN", "NVIDIA GPU-UNKNOWN")


if __name__ == "__main__":
    unittest.main()
