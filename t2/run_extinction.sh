#!/usr/bin/env bash
# T2 extinction sweep (Beer-Lambert oracle); exit code = test result.
set -euo pipefail
out=$(blender -b --factory-startup --python-exit-code 1 --python "$(dirname "$0")/extinction_sweep.py" 2>&1) \
  && rc=0 || rc=$?
echo "$out" | grep -E "km|PASS|FAIL|Error|Traceback" || true
exit $rc
