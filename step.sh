#!/bin/bash

THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
set -e

BUILD_NUMBER=$(/usr/libexec/PlistBuddy -c 'print ":CFBundleVersion"' "${jira_plist_path}" 2>/dev/null)

python "${THIS_SCRIPT_DIR}/step.py" "${BUILD_NUMBER}"
exit $?