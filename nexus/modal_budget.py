"""Transparent planning math for the NEXUS Modal workload.

These are estimates derived from the worker's per-batch GPU guard and an
operational reserve. They do not cap workspace billing.
"""

DEFAULT_MONTHLY_VIDEO_TARGET = 22
DEFAULT_MODAL_CREDIT_USD = 30.00
DEFAULT_GPU_BUDGET_PER_BATCH_USD = 0.42
DEFAULT_CPU_MEMORY_RESERVE_PER_BATCH_USD = 0.08


def estimate_monthly_modal_budget(
    video_count=DEFAULT_MONTHLY_VIDEO_TARGET,
    monthly_credit_usd=DEFAULT_MODAL_CREDIT_USD,
    gpu_budget_per_video_usd=DEFAULT_GPU_BUDGET_PER_BATCH_USD,
    reserve_per_video_usd=DEFAULT_CPU_MEMORY_RESERVE_PER_BATCH_USD,
):
    """Return conservative planning totals, not billing guarantees."""
    video_count = int(video_count)
    monthly_credit_usd = float(monthly_credit_usd)
    gpu_budget_per_video_usd = float(gpu_budget_per_video_usd)
    reserve_per_video_usd = float(reserve_per_video_usd)
    if video_count < 0:
        raise ValueError("video_count cannot be negative")
    if monthly_credit_usd < 0 or gpu_budget_per_video_usd < 0 or reserve_per_video_usd < 0:
        raise ValueError("budget values cannot be negative")

    monthly_gpu_usd = round(video_count * gpu_budget_per_video_usd, 2)
    monthly_envelope_usd = round(
        video_count * (gpu_budget_per_video_usd + reserve_per_video_usd), 2
    )
    return {
        "video_count": video_count,
        "monthly_credit_usd": round(monthly_credit_usd, 2),
        "gpu_per_video_usd": round(gpu_budget_per_video_usd, 2),
        "reserve_per_video_usd": round(reserve_per_video_usd, 2),
        "monthly_gpu_usd": monthly_gpu_usd,
        "monthly_envelope_usd": monthly_envelope_usd,
        "credit_remaining_usd": round(monthly_credit_usd - monthly_envelope_usd, 2),
        "reserve_is_hard_cap": False,
        "workspace_billing_is_capped": False,
    }
