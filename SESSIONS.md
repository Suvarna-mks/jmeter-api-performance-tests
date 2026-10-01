# Sessions

| # | Date | What was added |
|---|---|---|
| 1 | 2026-10-01 | Local Node shop API, `plans/smoke.jmx` (token extraction, response/JSONPath/duration assertions, -J properties), `run.sh` smoke/load profiles with HTML report, `check_results.py` gate (error rate + per-endpoint p95), 6 pytest tests. Broke the app with a slow `/search` to check the gate fails |

Next: GitHub Actions workflow (setup Java, download JMeter, `./run.sh smoke`, upload `report/`) + badge.
