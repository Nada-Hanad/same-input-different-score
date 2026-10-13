#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$TASK_ROOT"
python3 reproducibility_artifact/scripts/validate.py
python3 -m unittest discover -s reproducibility_artifact/scripts -p 'test_*.py' -v
npm --prefix research_companion test
npm --prefix research_companion run build
