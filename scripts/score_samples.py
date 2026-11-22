"""Score every samples/*.txt with the live rubric and print a ranking.  (Milestone 2)

Usage: python scripts/score_samples.py [--only NAME]

- First line of each sample may be "Title | Company | Location" (optional);
  the rest is the description.
- Builds a Job (source="jsearch", job_id="sample:{stem}") and calls scorer.score_job.
- Prints a table sorted by final score: file, score, verdict, top 3 deductions, summary.
- Writes data/sample_scores.csv (data/ is gitignored).
- Does not touch SQLite, Sheets or notifications.
"""

raise SystemExit("Milestone 2: implement scripts/score_samples.py")
