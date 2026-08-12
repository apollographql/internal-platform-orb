#!/bin/bash

scratch=$(mktemp -d -t tmp.XXXXXXXXXX)
finish() {
	rm -rf "$scratch"
}
trap finish EXIT

PAYLOAD_FILE=$scratch/payload.json

BuildMessageBody() {
	echo "Build message body..."
	if ! command -v envsubst >/dev/null 2>&1; then
		echo 'Ensure that `gettext-base` is available on the system, so that `envsubst` is available.'
		exit 1
	fi

	# Everything below runs in one subshell with obviously-secret-named vars
	# unset first, so that feature can't naively expose a token/key/password.
	# From here on, the payload is only ever mutated via `jq` on the file --
	# no more shell text-substitution/escaping passes for quoting mistakes to
	# hide in.
	(
		for secret_var in $(env | cut -d= -f1 | grep -E -i '(^|_)(TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL)($|_)' || true); do
			unset "$secret_var"
		done

		# Safe read only -- not an expansion. $SLACK_PARAM_CUSTOM/$SLACK_PARAM_CHANNEL
		# are fixed, hardcoded tokens; envsubst just looks them up (avoiding echo's
		# backslash-mangling). The template's own placeholders (${COMMIT_MESSAGE},
		# $CIRCLE_USERNAME, etc.) are still untouched after this.
		printf '%s\n' '$SLACK_PARAM_CUSTOM' | envsubst >"$PAYLOAD_FILE"
		CH=$(printf '%s\n' '$SLACK_PARAM_CHANNEL' | envsubst)

		# Text defaults to "" only if the custom body doesn't already set it;
		# channel is always authoritative from the parameter, even if the
		# custom body happens to define its own "channel" key.
		jq --arg ch "$CH" '{"text": ""} + . + {"channel": $ch}' "$PAYLOAD_FILE" >"$PAYLOAD_FILE.tmp" || exit 1
		mv "$PAYLOAD_FILE.tmp" "$PAYLOAD_FILE" || exit 1

		# Fail fast if the caller's own static template isn't valid JSON.
		jq empty "$PAYLOAD_FILE" || {
			echo "ERROR: template is not valid JSON"
			exit 1
		}

		# The one and only expansion. Every string leaf gets exactly one
		# envsubst pass, then goes back in via jq --arg (JSON-escapes on the
		# way in, so this can't break the JSON regardless of content). No
		# further pass, no recursion into whatever comes out of this one.
		jq -c 'paths(type == "string")' "$PAYLOAD_FILE" | while IFS= read -r path; do
			value=$(jq -r --argjson p "$path" 'getpath($p)' "$PAYLOAD_FILE")
			expanded=$(printf '%s\n' "$value" | envsubst)
			jq --argjson p "$path" --arg v "$expanded" 'setpath($p; $v)' "$PAYLOAD_FILE" \
				>"$PAYLOAD_FILE.tmp" || exit 1
			mv "$PAYLOAD_FILE.tmp" "$PAYLOAD_FILE" || exit 1
		done
	)
	build_status=$?
	# `exit` inside the subshell above only terminates that subshell -- repeat
	# its exit code here so a build failure (e.g. the `jq empty` check) actually
	# fails this step instead of silently continuing to PostToSlack.
	if [ "$build_status" -ne 0 ]; then
		exit "$build_status"
	fi
}

PostToSlack() {
	echo "Sending body...: $(cat "$PAYLOAD_FILE")"
	SLACK_SENT_RESPONSE=$(curl -s -f -X POST -H 'Content-type: application/json' -H "Authorization: Bearer $SLACK_ACCESS_TOKEN" --data-binary "@$PAYLOAD_FILE" https://slack.com/api/chat.postMessage)
	SLACK_ERROR_MSG=$(echo "$SLACK_SENT_RESPONSE" | jq '.error')
	if [ ! "$SLACK_ERROR_MSG" = "null" ]; then
		echo "Slack API returned an error message:"
		echo "$SLACK_ERROR_MSG"
		exit 1
	fi
}

ShouldPost() {
	if ! [[ ("$CCI_STATUS" = "$SLACK_PARAM_EVENT") || ("$SLACK_PARAM_EVENT" = "always") ]]; then
		echo "NO SLACK ALERT"
		echo
		echo "This command is set to send an alert on: $SLACK_PARAM_EVENT"
		echo "Current status: ${CCI_STATUS}"
		exit 0
	fi
}

# Will not run if sourced from another script.
# This is done so this script may be tested.
ORB_TEST_ENV="bats-core"
if [ "${0#*"$ORB_TEST_ENV"}" = "$0" ]; then
	set -euo pipefail
	. "/tmp/SLACK_JOB_STATUS"
	ShouldPost
	BuildMessageBody
	PostToSlack
fi
