"""Data contracts passed between Zoe's modules.

Change these deliberately: every module and test depends on them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, HttpUrl, field_validator


def _to_utc(value: datetime) -> datetime:
    """Naive datetimes are taken as UTC; aware ones are converted to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_to_utc)]


class Job(BaseModel):
    """One job posting, normalized from any source."""

    job_id: str = Field(description='Stable ID: "{source}:{source_native_id}"')
    source: Literal["jsearch", "gmail_alerts"]
    title: str
    company: str
    location: str | None = None
    remote: bool | None = None
    pay_min: float | None = None
    pay_max: float | None = None
    pay_period: Literal["hour", "year"] | None = None
    posted_at: UtcDatetime | None = Field(default=None, description="UTC")
    apply_url: HttpUrl | None = None
    canonical_url: str | None = Field(default=None, description="Used for cross-source dedupe")
    description: str = ""
    description_source: Literal["full", "snippet"] = "full"
    publisher: str | None = Field(default=None, description="e.g. ZipRecruiter, Indeed")
    search_name: str | None = Field(default=None, description="Which config search found it")

    @field_validator("job_id")
    @classmethod
    def _job_id_shape(cls, v: str) -> str:
        prefix, sep, native = v.partition(":")
        if not (sep and prefix.strip() and native.strip()):
            raise ValueError('job_id must look like "<source>:<native_id>"')
        return v


class DeductionCode(StrEnum):
    DEALBREAKER = "DEALBREAKER"
    MUST_HAVE_MISSING = "MUST_HAVE_MISSING"
    SENIORITY_MISMATCH = "SENIORITY_MISMATCH"
    COMP_BELOW_FLOOR = "COMP_BELOW_FLOOR"
    LOCATION_MISMATCH = "LOCATION_MISMATCH"
    NICE_TO_HAVE_MISSING = "NICE_TO_HAVE_MISSING"
    DOMAIN_GAP = "DOMAIN_GAP"
    VAGUE_POSTING = "VAGUE_POSTING"
    SNIPPET_ONLY = "SNIPPET_ONLY"
    RED_FLAG = "RED_FLAG"


# Points per deduction and the max total per code. Mirrors prompts/scorer_system.md.
DEDUCTION_RULES: dict[DeductionCode, tuple[int, int]] = {
    DeductionCode.DEALBREAKER: (100, 100),
    DeductionCode.MUST_HAVE_MISSING: (30, 60),
    DeductionCode.SENIORITY_MISMATCH: (25, 25),
    DeductionCode.COMP_BELOW_FLOOR: (25, 25),
    DeductionCode.LOCATION_MISMATCH: (20, 20),
    DeductionCode.NICE_TO_HAVE_MISSING: (5, 15),
    DeductionCode.DOMAIN_GAP: (10, 10),
    DeductionCode.VAGUE_POSTING: (10, 10),
    DeductionCode.SNIPPET_ONLY: (10, 10),
    DeductionCode.RED_FLAG: (10, 20),
}
assert set(DEDUCTION_RULES) == set(DeductionCode), "every DeductionCode needs a rule"

# Verdict thresholds. Mirror the "Verdict" section of prompts/scorer_system.md.
APPLY_NOW_MIN = 80
REVIEW_MIN = 60


class Deduction(BaseModel):
    code: DeductionCode
    detail: str = Field(description="What is missing or wrong, in a few words")
    job_evidence: str = Field(description="Short quote from the posting")
    profile_evidence: str = Field(description='What the profile says, or "profile is silent"')


class Verdict(StrEnum):
    APPLY_NOW = "apply_now"
    REVIEW = "review"
    SKIP = "skip"


class ScoreResult(BaseModel):
    """What the scoring model must return (used as the forced tool's input schema)."""

    deductions: list[Deduction]
    strengths: list[str] = Field(description="Top reasons he fits; do not affect score")
    missing_skills: list[str]
    match_score: int = Field(ge=0, le=100, description="Model's own computed score")
    verdict: Verdict
    summary: str = Field(description="One sentence, phone-lock-screen length")


def compute_score(deductions: list[Deduction]) -> int:
    """Recompute the score in code: 100 minus capped deductions, clamped 0–100."""
    totals: dict[DeductionCode, int] = {}
    for d in deductions:
        points, cap = DEDUCTION_RULES[d.code]
        totals[d.code] = min(totals.get(d.code, 0) + points, cap)
    return max(0, min(100, 100 - sum(totals.values())))


def verdict_for(score: int, deductions: list[Deduction]) -> Verdict:
    if any(d.code is DeductionCode.DEALBREAKER for d in deductions) or score < REVIEW_MIN:
        return Verdict.SKIP
    return Verdict.APPLY_NOW if score >= APPLY_NOW_MIN else Verdict.REVIEW


class StoredScore(BaseModel):
    """A ScoreResult plus the code-computed score and bookkeeping, as saved in SQLite."""

    job_id: str
    result: ScoreResult
    final_score: int
    final_verdict: Verdict
    model: str
    rubric_version: int
    scored_at: UtcDatetime


class RunSummary(BaseModel):
    started_at: UtcDatetime
    finished_at: UtcDatetime | None = None
    status: Literal["ok", "partial", "failed", "skipped_schedule"] = "ok"
    fetched: int = 0
    new: int = 0
    scored: int = 0
    alerted: int = 0
    sheet_rows_written: int = 0
    errors: list[str] = Field(default_factory=list)
