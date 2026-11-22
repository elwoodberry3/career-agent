"""JSearch (RapidAPI) source.  (Milestone 4)

Before coding: check JSearch's current docs on RapidAPI for the endpoint,
query parameters and response fields. The notes below are a starting point only.

Expected shape (verify):
    GET https://{RAPIDAPI_HOST}/search
        params: query="{search.query} in {search.location}", page=1, num_pages=1,
                date_posted=settings.sources.jsearch.date_posted, country, remote_jobs_only
        headers: X-RapidAPI-Key, X-RapidAPI-Host
    response["data"][i]: job_id, job_title, employer_name, job_city, job_state,
        job_is_remote, job_min_salary, job_max_salary, job_salary_period,
        job_posted_at_datetime_utc, job_apply_link, job_description, job_publisher

Contract:
    class JSearchSource(JobSource): __init__(settings, http: httpx.Client | None = None)
    lookup(title, company) -> Job | None     # used by gmail_alerts enrichment

- Map to Job with job_id = f"jsearch:{job_id}", search_name = search.name.
- Backoff on 429/5xx, 3 attempts; then raise SourceError.
- `python -m zoe.ingest.jsearch --print` prints today's jobs (title | company | publisher).
- Tests use JSON fixtures in tests/fixtures/jsearch_*.json and a mocked httpx transport.
"""

from __future__ import annotations


class JSearchSource:
    name = "jsearch"

    def __init__(self, settings, http=None):
        raise NotImplementedError("Milestone 4")
