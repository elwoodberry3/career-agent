"""Score a Job against the candidate profile with Claude.  (Milestone 2)

Contract:
    score_job(job: Job, profile_text: str, settings, client=None) -> StoredScore

- System prompt: settings.scoring.prompt_path (prompts/scorer_system.md).
- User message: "CANDIDATE PROFILE" section + "JOB POSTING" section (title, company,
  location, pay, remote, description_source, description).
- Force structured output with a single tool named "submit_score" whose
  input_schema is ScoreResult.model_json_schema(), and tool_choice forcing it.
- Validate the tool input with ScoreResult.model_validate. On failure, retry once
  with the validation error appended; then raise ScoringError.
- final_score = models.compute_score(result.deductions)
  final_verdict = models.verdict_for(final_score, result.deductions)
  (the model's match_score is kept in result for debugging only).
- `client` is injectable (an anthropic.Anthropic) so tests can pass a mock.
- Retry with backoff on rate-limit / overloaded errors (max 3).
"""

from __future__ import annotations


class ScoringError(RuntimeError):
    pass


def score_job(job, profile_text: str, settings, client=None):
    raise NotImplementedError("Milestone 2")
