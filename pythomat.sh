#!/usr/bin/env sh
set -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -d "${SCRIPT_DIR}/venv" ]; then
  echo "Creating virtual environment and installing dependencies…"
  python3 -m venv venv
  source "${SCRIPT_DIR}/venv/bin/activate"
  pip3 install .

  echo "Running Pythomat…"
fi

source "${SCRIPT_DIR}/venv/bin/activate"
python3 "${SCRIPT_DIR}/pythomat.py" $@
