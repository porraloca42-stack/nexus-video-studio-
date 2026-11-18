import unittest

from nexus.modal_budget import estimate_monthly_modal_budget


class ModalBudgetProjectionTests(unittest.TestCase):
    def test_default_monthly_projection_for_22_videos(self):
        projection = estimate_monthly_modal_budget()
        self.assertEqual(projection["monthly_gpu_usd"], 9.24)
        self.assertEqual(projection["monthly_envelope_usd"], 11.00)
        self.assertEqual(projection["credit_remaining_usd"], 19.00)
        self.assertFalse(projection["reserve_is_hard_cap"])
        self.assertFalse(projection["workspace_billing_is_capped"])

    def test_custom_video_target_and_credit(self):
        projection = estimate_monthly_modal_budget(
            video_count=10,
            monthly_credit_usd=20,
            gpu_budget_per_video_usd=0.30,
            reserve_per_video_usd=0.05,
        )
        self.assertEqual(projection["monthly_gpu_usd"], 3.00)
        self.assertEqual(projection["monthly_envelope_usd"], 3.50)
        self.assertEqual(projection["credit_remaining_usd"], 16.50)

    def test_rejects_negative_inputs(self):
        with self.assertRaises(ValueError):
            estimate_monthly_modal_budget(video_count=-1)
        with self.assertRaises(ValueError):
            estimate_monthly_modal_budget(monthly_credit_usd=-1)


if __name__ == "__main__":
    unittest.main()
