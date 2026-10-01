# jmeter-api-performance-tests

JMeter performance tests for a small shop API, run from the command line, with an HTML report and a Python check that fails the run when error rate or p95 latency goes over budget.

## Why I built this

JMeter shows up in a lot of QA job descriptions, and most JMeter tutorials stop at "click Run in the GUI and look at the graph". In a real pipeline nobody looks at the graph. The run has to pass or fail on its own. I wanted a setup where the test plan is a file in git, it runs headless, and a number decides if the build is green.

I test against a tiny local API (`demo-api/server.js`) instead of a public site, because load testing someone else's server without permission is not OK.

## What's in it

- `plans/smoke.jmx`: one JMeter plan for the main flow: health → product list → login → orders with the token → search
  - JSON Extractor pulls the login token, and a Header Manager sends it as `Bearer ${token}`
  - Response assertions on status codes, a JSONPath assertion on the product list, and a Duration assertion on `/search`
  - Users, loops, ramp-up, host and port all come from `-J` properties, so the same plan works for smoke and load
- `run.sh`: starts the API, runs JMeter in non-GUI mode, builds the HTML dashboard, then runs the check
- `check_results.py`: reads the `.jtl` file and fails if error rate > 1% or p95 is over the limit in `thresholds.json` (per endpoint, with a default)
- `tests/`: pytest tests for the checker, using small hand-made `.jtl` files

## Run it

Needs Node, Python 3, Java and JMeter (`brew install jmeter`).

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                 # tests for the threshold checker

./run.sh smoke         # 3 users x 2 loops
./run.sh load          # 30 users x 20 loops, 10s ramp-up
open report/load/index.html
```

Smoke output:

```
label                   count  errors  avg ms  p95 ms
GET /health                 6       0       6      19
GET /orders (auth)          6       0       1       2
GET /products               6       0       2       3
GET /search                 6       0      53      54
POST /login                 6       0       2       3
PASS: all thresholds met
```

To see it fail, make search slow: `SEARCH_DELAY_MS=400 ./run.sh smoke`

```
FAIL: error rate 20.0% > 1.0%
FAIL: GET /search: p95 405 ms > 300 ms
```

(exit code 1, so CI would go red)

## What I learned

- A `.jmx` file is just XML. Every element is followed by a `<hashTree>` holding its children, which is how assertions and extractors attach to one request.
- `${__P(users,3)}` reads a `-Jusers=` property with a default, so one plan covers smoke and load and I don't have to keep two copies in sync.
- The JSON Extractor default value (`NO_TOKEN`) matters: if login breaks, the next request fails with 401 instead of sending an empty header that's harder to debug.
- A Duration assertion turns "slow" into "failed", so slowness also shows up in the error rate, not only in the latency numbers.
- Average latency hides problems. With 5 fast calls and 1 slow one the average looks fine, but p95 shows it. That's why the gate uses p95.

## Known limitations / TODO

- p95 uses nearest-rank, which is rough with very few samples.
- The demo API is in-memory, so the numbers are much faster than a real service with a database.
- Only one thread group. A real mix (80% browse, 20% checkout) needs separate groups or a Throughput Controller.
- TODO: GitHub Actions workflow that installs JMeter, runs `./run.sh smoke` and uploads the HTML report.
- TODO: CSV Data Set Config with many test users instead of one hard-coded login.
