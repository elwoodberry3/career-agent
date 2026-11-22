from zoe.models import (
    Deduction,
    DeductionCode,
    Job,
    ScoreResult,
    Verdict,
    compute_score,
    verdict_for,
)


def d(code: DeductionCode) -> Deduction:
    return Deduction(code=code, detail="x", job_evidence="x", profile_evidence="x")


def test_no_deductions_is_100():
    assert compute_score([]) == 100


def test_caps_apply_per_code():
    # three must-haves missing = 90 raw, capped at 60
    assert compute_score([d(DeductionCode.MUST_HAVE_MISSING)] * 3) == 40
    # four nice-to-haves = 20 raw, capped at 15
    assert compute_score([d(DeductionCode.NICE_TO_HAVE_MISSING)] * 4) == 85


def test_score_clamps_at_zero():
    deds = [d(DeductionCode.DEALBREAKER), d(DeductionCode.SENIORITY_MISMATCH)]
    assert compute_score(deds) == 0


def test_verdicts():
    assert verdict_for(85, []) is Verdict.APPLY_NOW
    assert verdict_for(70, []) is Verdict.REVIEW
    assert verdict_for(59, []) is Verdict.SKIP
    assert verdict_for(100, [d(DeductionCode.DEALBREAKER)]) is Verdict.SKIP


def test_score_result_schema_is_tool_ready():
    schema = ScoreResult.model_json_schema()
    assert schema["type"] == "object"
    assert {"deductions", "verdict", "summary"} <= set(schema["properties"])


def test_job_minimal():
    job = Job(job_id="jsearch:abc", source="jsearch", title="Creative Director", company="Acme")
    assert job.description_source == "full"
