"""
Router: /scores
================
GET /scores/calibration  — runs the human-calibration check and returns
                           Pearson and Spearman correlations between the
                           fused scorer and human ratings.

Individual score retrieval (GET /scores/{score_id}) can be added here
once the UI needs it.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/calibration", summary="Calibration report: fused score vs human ratings")
def get_calibration_report() -> dict:
    """
    Scores a set of hand-rated example answers through the live pipeline and
    reports the Pearson and Spearman correlation between the fused score and
    the human ratings.

    Use this endpoint to validate that the scorer tracks human judgment.
    A Pearson r > 0.8 is considered a strong agreement.

    **Response fields:**
    - `pearson_r`   — Pearson correlation coefficient (-1 to 1)
    - `spearman_r`  — Spearman rank correlation (-1 to 1)
    - `n_samples`   — number of samples scored
    - `pairs`       — per-sample breakdown (human vs fused score)
    """
    from app.services.calibration import run_calibration
    return run_calibration()
