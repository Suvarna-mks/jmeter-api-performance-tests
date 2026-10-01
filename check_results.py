"""Read a JMeter .jtl (CSV) file and fail if error rate or p95 latency is over budget.

Usage: python check_results.py results/smoke.jtl [thresholds.json]
"""
import csv
import json
import sys


def percentile(values, pct):
    # nearest-rank percentile, good enough for a CI gate
    if not values:
        return 0
    values = sorted(values)
    rank = max(1, round(pct / 100 * len(values)))
    return values[rank - 1]


def summarize(jtl_path):
    by_label = {}
    with open(jtl_path, newline="") as f:
        for row in csv.DictReader(f):
            s = by_label.setdefault(row["label"], {"elapsed": [], "errors": 0})
            s["elapsed"].append(int(row["elapsed"]))
            if row["success"].lower() != "true":
                s["errors"] += 1
    stats = {}
    for label, s in by_label.items():
        n = len(s["elapsed"])
        stats[label] = {
            "count": n,
            "errors": s["errors"],
            "avg_ms": round(sum(s["elapsed"]) / n),
            "p95_ms": percentile(s["elapsed"], 95),
        }
    return stats


def check(stats, thresholds):
    problems = []
    total = sum(s["count"] for s in stats.values())
    errors = sum(s["errors"] for s in stats.values())
    if total == 0:
        return ["no samples in the results file"]
    error_rate = errors / total
    if error_rate > thresholds["max_error_rate"]:
        problems.append(f"error rate {error_rate:.1%} > {thresholds['max_error_rate']:.1%}")
    p95_limits = thresholds.get("p95_ms", {})
    for label, s in stats.items():
        limit = p95_limits.get(label, p95_limits.get("default"))
        if limit is not None and s["p95_ms"] > limit:
            problems.append(f"{label}: p95 {s['p95_ms']} ms > {limit} ms")
    return problems


def main(argv):
    jtl = argv[1]
    thresholds_file = argv[2] if len(argv) > 2 else "thresholds.json"
    with open(thresholds_file) as f:
        thresholds = json.load(f)
    stats = summarize(jtl)
    print(f"{'label':<22}{'count':>7}{'errors':>8}{'avg ms':>8}{'p95 ms':>8}")
    for label, s in sorted(stats.items()):
        print(f"{label:<22}{s['count']:>7}{s['errors']:>8}{s['avg_ms']:>8}{s['p95_ms']:>8}")
    problems = check(stats, thresholds)
    for p in problems:
        print("FAIL:", p)
    if not problems:
        print("PASS: all thresholds met")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
