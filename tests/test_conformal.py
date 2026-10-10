import pytest
from hares.ai.conformal import ConformalCalibrator


def test_conformal_calibrator_initialization_defaults():
    calibrator = ConformalCalibrator()
    assert calibrator.alpha == 0.001
    assert calibrator.synthetic_threshold == 0.85
    assert calibrator.bonafide_threshold == 0.35


def test_conformal_calibrator_custom_calibration_distribution():
    # Synthetic calibration distribution where 99.9% of scores are below 0.80
    calibration_scores = [0.05 * (i / 1000) for i in range(1000)]
    calibrator = ConformalCalibrator(calibration_scores=calibration_scores, alpha=0.01)
    assert calibrator.alpha == 0.01
    assert calibrator.synthetic_threshold <= 0.06


def test_conformal_non_conformity_score_mapping():
    calibrator = ConformalCalibrator()
    # f_bonafide = 0.9 -> s(x) = 0.1 (low non-conformity)
    assert calibrator.compute_non_conformity_score(0.9) == 0.1
    # f_bonafide = 0.1 -> s(x) = 0.9 (high non-conformity)
    assert calibrator.compute_non_conformity_score(0.1) == 0.9
    # Bounded between 0 and 1
    assert calibrator.compute_non_conformity_score(-0.5) == 1.0
    assert calibrator.compute_non_conformity_score(1.5) == 0.0


def test_conformal_p_value_monotonicity():
    calibrator = ConformalCalibrator()
    p_high_conformity = calibrator.compute_p_value(0.1)  # Normal bonafide
    p_low_conformity = calibrator.compute_p_value(0.9)   # Extreme non-conformity
    assert p_high_conformity > p_low_conformity


def test_conformal_evaluation_tri_band_classification():
    calibrator = ConformalCalibrator(synthetic_threshold=0.85, bonafide_threshold=0.35)

    # 1. Extreme synthetic sample (bonafide_prob = 0.05 -> s = 0.95 >= 0.85)
    res_synthetic = calibrator.evaluate(bonafide_probability=0.05)
    assert res_synthetic["is_synthetic"] is True
    assert res_synthetic["is_abstaining"] is False
    assert res_synthetic["non_conformity_score"] >= 0.85

    # 2. Authentic citizen sample (bonafide_prob = 0.90 -> s = 0.10 <= 0.35)
    res_bonafide = calibrator.evaluate(bonafide_probability=0.90)
    assert res_bonafide["is_synthetic"] is False
    assert res_bonafide["is_abstaining"] is False
    assert res_bonafide["non_conformity_score"] <= 0.35

    # 3. Ambiguous sample in uncertainty band (bonafide_prob = 0.40 -> s = 0.60)
    # 0.35 < 0.60 < 0.85 -> Abstain (routes to Amber)
    res_ambiguous = calibrator.evaluate(bonafide_probability=0.40)
    assert res_ambiguous["is_synthetic"] is False
    assert res_ambiguous["is_abstaining"] is True
