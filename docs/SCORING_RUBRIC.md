# Scoring rubric — why it works this way

The live prompt is `prompts/scorer_system.md`. This file explains it.

## The problem

Ask an LLM "score this job 0–100" and it gives 75–85 to almost everything that
shares a few keywords with the resume. A threshold of 75 then alerts on half the
feed, and alerts get ignored.

## The fix

1. **Deductive, not additive.** Start at 100 and subtract for specific, named
   problems. Strengths are reported but never add points.
2. **Evidence required.** Every deduction cites a quote from the posting, so
   Steve can check a score in seconds and spot rubric bugs.
3. **Code does the math.** `scorer.py` recomputes `100 − sum(deductions)`,
   applies the per-code caps, and clamps to 0–100. The model's own number is
   stored as `model_reported_score` for debugging but not used.
4. **Dealbreakers are absolute.** One dealbreaker = score 0 = verdict `skip`.

## Calibration loop

1. Score `samples/` with `python scripts/score_samples.py`.
2. Compare to Steve's gut ranking. Where they disagree, look at the deductions:
   - Wrong deduction applied → tighten that row's "When" wording in the prompt.
   - Right deduction, wrong weight → change the number.
   - Missing concept → add a row.
3. Commit prompt changes with a note on what moved (`prompt: SENIORITY −25→−20`).
4. During Milestone 8, use the Sheet's `Status` column as ground truth and set
   `notify.threshold` from real data.

`ScoreResult.rubric_version` (from `config.yaml → scoring.rubric_version`) is
stored with every score so old and new rubric results can be told apart.
Bump it whenever the prompt changes meaningfully.
