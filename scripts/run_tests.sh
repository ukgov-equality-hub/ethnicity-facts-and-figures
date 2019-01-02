#!/bin/bash
#
# Run project tests
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_tests.sh

# Use default environment vars for localhost if not already set

set -o pipefail

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

npm test
display_result $? 3 "JS tests"

black --check .
display_result $? 1 "Code style check"

flake8 .
display_result $? 4 "Python code lint check"

npx gulp
display_result $? 2 "Frontend asset build check"

py.test --cov application/ --cov-report term-missing
pytest_exitcode=$?

display_result ${pytest_exitcode} 3 "Python tests"
if [[ "${pytest_exitcode}" == "0" ]] && [[ "${CI}" ]]; then
  coveralls
fi
