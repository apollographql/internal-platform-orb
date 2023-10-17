# CircleCI Maintenance Scripts

## `long_running_workflows.py`

Finds any Circle Workflow that's too old. If commit is set to true, goes ahead and cancels them via the API.

Outputs findings into /tmp/circleci-long-running-workflows.tsv

## `main_is_borked.py`

Is main b0rked? Ping our on call staff and the person who authored the latest commit...
