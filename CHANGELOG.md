# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.0.12] - 2023-01-20
### Added
  - circleci-stop-if command

### Changed
  - modifications to this orb now require updated CHANGELOG. Versions before this point will be documented in a best effort approach, going forward changelog entries are enforced.
  - slack-circleci-build has an optional who-did-it parameter which allows overriding author information


## [1.0.11] - 2023-01-03

### Changed
  - slack-circleci-build has an optional link parameter in case the default Circle URL does not work for your use case


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
