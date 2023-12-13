# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.3] - 2023-12-13

- Tweaked `enrich-mustache{,-folder}` commands to operate in environments where `PATH` does not include `$HOME/.local/bin`.

## [1.4.3] - 2023-12-06

- Updated the version of an orb used in CI to build this orb. The CI process that builds this orb requires a version bump + changelog to update the repo, so issuing a new version to update the build process.

## [1.4.2] - 2023-12-01

- No-Op change to add codeowners to the underlying repo. No changes made to functionality of orb.

## [1.4.1] - 2023-10-18

- Fixed `circleci-long-running-workflows` the parametrized mustache templating didn't respect newlines. Bugs like "unrecognized command --cancel" etc.

## [1.4.0] - 2023-10-18

- Deprecated `circleci-continue-long-job-cancel`
- Refactored `circleci-long-job-cancel` to `circleci-long-running-workflows`
  - Now takes a simple `window-start` and `window-end` set of arguments
  - No longer auto-cancels anything. Instead, provides the flag `cancel`
  - What is done with the output _afterwards_ is up to the user of the command
  - Moved output from `/tmp/notifications.tsv` to `/tmp/circle-long-running-workflows.tsv`
    - Format for output is now: `orgreposlug\tid\tusername\tname`
  - Example of new usage can be:
    - Warnings:
      - Run the command with `window-start-in-hours` as 2, and `window-end-in-hours` as 1
      - Using `slack-notify-compact`, you can then pipe the notifications to your team that you will be cancelling their workflows in a few hours
    - Cancels:
      - Run the command with `window-start-in-hours` as 4, and `window-end-in-hours` as 2, and `cancel` as true

## [1.3.3] - 2023-10-16

- Fixed `long_job_canceller` script to log moderately more. This fixes issues in CircleCI when it doesn't see output for too long due to no output detected.

## [1.3.2] - 2023-10-16

- Added `circleci-long-job-cancel` as a way to spin off `circleci-continue-long-job-cancel` for workflows looking to avoid using `continue` based workflows.
- Fixed `long_job_canceller` script to log moderately more. This fixes issues in CircleCI when it doesn't see output for too long due to no output detected.

## [1.3.1] - 2023-08-04

- Added `gcp-oidc-authorize` as a new option for authenticating to GCP. This uses Open Identity Connect (OIDC) and the Identity Provider (IdP) that Circle makes available to jobs to authenticate to GCP via GCP's Workload Identity Federation. See [Circle's Docs](https://circleci.com/docs/openid-connect-tokens/#google-cloud-platform) for more info

## [1.2.7] - 2023-07-07

- `enrich-mustache-from-path-file` now includes a `pre-process-command` which is executed right before rendering the specified config file's mustache template. On a side note, have you heard about `jq`'s `+` operator?
- `gcp-authorize` now works on MacOS based executors
- `circleci-stop-if-not`, to compliment `circleci-stop-if`

## [1.2.6] - 2023-06-23

- `github-bot-comment-on-pr` (command) and `alert-github` (job) better handle comments that are too long for inline Github PR comments. You may post to a secret gist (use the "report.md" option), or print inline (using the "print" option, the default), by using the `overlarge-content-to` parameter.

## [1.2.5] - 2023-05-31

- `github-bot-comment-on-pr` can now update comments with longer text without running into command line length limits.

## [1.2.4] - 2023-05-18

- circleci-job-cancelled "`main_is_borked`" script only alerts on awaiting approval jobs "to prod?" vs previous logic (which was targetting anything not our first (internal) deploy environment. This should be more generic and avoid some issues internally we were seeing with alerting people about irrelevant things.

## [1.2.3] - 2023-05-18

- setup command no longer saves the downloaded files as artifacts in Circle.

## [1.2.2] - 2023-05-11

- The command for `github-bot-comment-on-pr` may write `report.md` in addition to `/tmp/notification.txt`; if it does, it is posted as a secret GitHub Gist and linked from the comment.

## [1.2.1] - 2023-05-11

- Add optional argument to alert-github and github-bot-comment-on-pr `update-last` that will update the last comment instead of deleting and adding a new comment.
- Add optional argument to github-bot-delete-bot-comments `skip-last` that will delete all but the last comment.

## [1.1.0] - 2023-03-20

- Only fail tflint checks when error occurs instead of warnings

## [1.0.22] - 2023-02-24

### Changed

- The command `circleci-continue-long-job-cancel` now recognizes all workflows which have not been stopped. This will pick up ALL long running CircleCI Jobs, and not just ones which are `on-hold`

## [1.0.21] - 2023-02-22

### Changed

- Added optional argument to GitHub commands to let them be configured to run even if prior steps failed

## [1.0.20] - 2023-02-06

### Added

- The command `circleci-continue-long-job-cancel` can ignore - that is not emit age warnings - for workflows where all the on hold (aka yet to be approved approval jobs) have a name containing specified words

## [1.0.19] - 2023-02-06

### Fixed

- 1.0.13 introduced a bug with `circleci-continue-long-job-cancel`'s ability to correctly fetch user
  info for better Slack messages.

## [1.0.18] - 2023-02-03

### Fixed

- further reduce the size of code generated during `slack-notify-compact` command
- setup command only downloads repository once

## [1.0.17] - 2023-01-27

### Fixed

- 1.0.13 introduced a bug with `circleci-continue-long-job-cancel`'s datetime comparisons.

## [1.0.16] - 2023-01-27

### Fixed

- 1.0.14 introduced a bug with some Python `requests` helpers.

## [1.0.15] - 2023-01-27

### Fixed

- 1.0.14 introduced a bug in the way that our Python scripts function in regards to argument parsing.

## [1.0.14] - 2023-01-27

### Added

- Alerting included now for errors originating from CircleCI
- Command: `circleci-continue-long-job-cancel`
  - `--n-windows` argument:
    - Allows for setting how many windows for the continue CircleCI crawler to walk back across
    - Default: 6 (12 hours, each window is 2 hours in length)

## [1.0.13] - 2023-01-23

### Fixed

- The Command `circleci-continue-long-job-cancel` did not have the ability to properly paginate
  over results. This release makes it such that the Cancel command will now walk over a period of
  time, instead of a set number of pages.

## [1.0.12] - 2023-01-20

### Added

- `circleci-stop-if` command

### Changed

- modifications to this orb now require updated CHANGELOG. Versions before this point will be documented in a best effort approach, going forward changelog entries are enforced.
- `slack-circleci-build` has an optional who-did-it parameter which allows overriding author information

## [1.0.11] - 2023-01-03

### Changed

- `slack-circleci-build` has an optional link parameter in case the default Circle URL does not work for your use case

## [1.0.10] - 2022-12-07

### Changed

- the long job canceller script has the following changes:
  - better handles failures on branches that have not been pushed to
  - handle situation where robot makes a commit and human merges it (page the human)
  - don't warn robots to take action

## [1.0.8] - 2022-11-30

### Changed

- build fix

## [1.0.7] - 2023-11-30

### Added

- enrich-mustache-folder command
- git-diff-set-parameters command
- enrich-mustache-from-path-filter job

### Changed

- better documentation for enrich-mustache command
