#!/bin/bash
# Usage: ./run.sh smoke|load
# Starts the demo API, runs the JMeter plan, builds the HTML report and checks thresholds.
set -e
PROFILE=${1:-smoke}
case $PROFILE in
  smoke) PROPS="-Jusers=3 -Jloops=2 -Jrampup=1" ;;
  load)  PROPS="-Jusers=30 -Jloops=20 -Jrampup=10" ;;
  *) echo "unknown profile: $PROFILE (use smoke or load)"; exit 2 ;;
esac

node demo-api/server.js > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
sleep 1

rm -rf "results/$PROFILE.jtl" "report/$PROFILE"
mkdir -p results report
jmeter -n -t plans/smoke.jmx $PROPS \
  -Jjmeter.save.saveservice.output_format=csv \
  -l "results/$PROFILE.jtl" -e -o "report/$PROFILE"

python3 check_results.py "results/$PROFILE.jtl" thresholds.json
