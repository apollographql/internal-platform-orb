#!/usr/bin/env node
"use strict";

const SECRET_VAR_RE = /(^|_)(TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL)($|_)/i;

function buildMessageBody() {
  console.log("Build message body...");

  // Strip anything shaped like a secret before expanding placeholders, so a
  // custom template can't naively expose a token/key/password.
  const safeEnv = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (!SECRET_VAR_RE.test(key)) safeEnv[key] = value;
  }

  const rawCustom = safeEnv.SLACK_PARAM_CUSTOM || "";
  const channel = safeEnv.SLACK_PARAM_CHANNEL || "";

  let template;
  try {
    template = JSON.parse(rawCustom);
  } catch {
    console.error("ERROR: template is not valid JSON");
    process.exit(1);
  }

  const merged = { text: "", ...template, channel };

  return JSON.stringify(merged, (_, v) =>
    typeof v === "string"
      ? v.replace(
          /\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g,
          (_, braced, bare) => safeEnv[braced || bare] ?? "",
        )
      : v,
  );
}

async function postToSlack(body) {
  console.log(`Sending body...: ${body}`);

  const response = await fetch("https://slack.com/api/chat.postMessage", {
    method: "POST",
    headers: {
      "Content-type": "application/json",
      Authorization: `Bearer ${process.env.SLACK_ACCESS_TOKEN}`,
    },
    body,
  });

  const result = await response.json();
  if (!response.ok || result.error) {
    console.log("Slack API returned an error message:");
    console.log(result.error ?? `HTTP ${response.status}`);
    process.exit(1);
  }
}

function shouldPost() {
  const status = process.env.CCI_STATUS;
  const event = process.env.SLACK_PARAM_EVENT;
  if (!(status === event || event === "always")) {
    console.log("NO SLACK ALERT");
    console.log("");
    console.log(`This command is set to send an alert on: ${event}`);
    console.log(`Current status: ${status}`);
    process.exit(0);
  }
}

async function main() {
  shouldPost();
  await postToSlack(buildMessageBody());
}

// Will not run if required from another script (e.g. tests).
if (require.main === module) {
  main();
}
