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


def test_every_deduction_code_has_a_rule():
    from zoe.models import DEDUCTION_RULES

    assert set(DEDUCTION_RULES) == set(DeductionCode)


def test_posted_at_normalized_to_utc():
    from datetime import UTC, datetime, timedelta, timezone

    naive = Job(
        job_id="jsearch:1", source="jsearch", title="t", company="c",
        posted_at=datetime(2026, 11, 21, 12, 0),
    )
    assert naive.posted_at == datetime(2026, 11, 21, 12, 0, tzinfo=UTC)

    chicago = timezone(timedelta(hours=-6))
    aware = Job(
        job_id="jsearch:2", source="jsearch", title="t", company="c",
        posted_at=datetime(2026, 11, 21, 6, 0, tzinfo=chicago),
    )
    assert aware.posted_at == datetime(2026, 11, 21, 12, 0, tzinfo=UTC)
    assert aware.posted_at.utcoffset() == timedelta(0)


def test_bad_job_id_rejected():
    import pytest
    from pydantic import ValidationError

    for bad in ("abc", ":x", "jsearch:", " : "):
        with pytest.raises(ValidationError):
            Job(job_id=bad, source="jsearch", title="t", company="c")


def test_score_result_schema_keeps_enums():
    schema = ScoreResult.model_json_schema()
    defs = schema["$defs"]
    assert set(defs["DeductionCode"]["enum"]) == {c.value for c in DeductionCode}
    assert set(defs["Verdict"]["enum"]) == {"apply_now", "review", "skip"}
