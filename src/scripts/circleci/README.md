# CircleCI Maintenance Scripts

## `long_running_workflows.py`

Finds any Circle Workflow that's too old. If `cancel` is set to true, goes ahead and cancels them via the API.

## `main_is_borked.py`

Is main b0rked? Ping our on call staff and the person who authored the latest commit...
