#!/bin/bash

# Will not run if sourced from another script.
# This is done so this script may be tested.
ORB_TEST_ENV="bats-core"
if [ "${0#*"$ORB_TEST_ENV"}" = "$0" ]; then
	. "/tmp/SLACK_JOB_STATUS"
	node "$(dirname "$0")/alert-slack-notify.js"
fi
