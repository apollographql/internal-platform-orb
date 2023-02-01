#!/usr/bin/env python3

from Modules.circle_utils import *
import datetime
import itertools
import os.path
import pprint
import requests
import sys


from dateutil.parser import *

import argparse

sys.path.append("..")  # added!


job_life_clock = datetime.timedelta(hours=2)
job_midlife_warning = datetime.timedelta(hours=1)
utc_tz = datetime.timezone(datetime.timedelta(hours=0))
now = datetime.datetime.now(utc_tz)

robot_committers = ["apollo-bot2"]


def get_workflow_started_by(current_workflow, headers):
    user_url = f"https://circleci.com/api/v2/user/{current_workflow['started_by']}"
    user_info = http_get(user_url, headers=headers).json()
    # the Github / CircleCI scheduling bot won't have a username (JSON body will be {'message': 'Not found.'})
    username = user_info.get("login", "")

    return username


def get_workflow_pending_approval_jobs(workflow_id, headers):
    """
    the top object of the workflow only tells us that the workflow is on hold, not why.
    Iterate through all the jobs of the workflow checking in particular for approval jobs
    and return information about approval jobs in this workflow that are on hold
    (so then we can filter them later)
    """

    for current_job in get_all_items(f"/workflow/{workflow_id}/job", headers):
        if (current_job.get("type") == "approval") and (current_job.get("status") == "on_hold"):
            yield current_job


def pipeline_created_at_to_datetime(pipeline):
    '''
    Pipeline's create_at value is in ISO 8601 format: Y-m-dTH:M:S.fZ, convert to a
    datetime.
    '''
    return datetime.datetime.fromisoformat(pipeline['created_at'][:-1]).replace(tzinfo=datetime.timezone.utc)


def find_old_workflow_ids(repo_slug, window_start, window_end, headers):
    print(f'Window to paginate through: [{window_start}, {window_end}]')
    for current_pipeline in get_all_items(f"/project/gh/{repo_slug}/pipeline", headers, None):
        # Paginate through only those pipelines which started inside our given window
        created_at = pipeline_created_at_to_datetime(current_pipeline)
        if window_end < created_at:
            print(f'Pipeline too young: {created_at}')
            continue
        if created_at < window_start:
            print(f'Pipeline too old: {created_at}')
            return None

        for current_workflow in get_all_items(f"/pipeline/{current_pipeline['id']}/workflow", headers, None):
            if current_workflow["status"] == "on_hold":
                created_at_str = current_workflow["created_at"]
                created_at = isoparse(created_at_str)

                if ((created_at < (now - job_midlife_warning)) and (created_at > (now - job_life_clock))):
                    username = get_workflow_started_by(
                        current_workflow, headers)
                    if username in robot_committers:
                        continue

                    yield {"job_status": "age_warning", "name": current_workflow['name'], "id": current_workflow['id'], "username": username}

                if (created_at < (now - job_life_clock)):
                    username = get_workflow_started_by(
                        current_workflow, headers)
                    yield {"job_status": "too_old", "name": current_workflow['name'], "id": current_workflow['id'], "username": username}


def filter_ignored_jobs(current_info, ignore, headers):
    pending_approvals = get_workflow_pending_approval_jobs(current_info['id'], headers)

    return list( itertools.dropwhile( lambda x: x['name'].find(ignore) > -1 , pending_approvals ) )


def main(circleapitoken, orgreposlug, n_windows, output_file, commit, ignore):
    standard_headers = {"Circle-Token": circleapitoken}

    simple_path = os.path.abspath(os.path.expanduser(
        os.path.expandvars(output_file)))

    with open(simple_path, 'w') as f:
        f.write("job_status\tproceed\tid\tusername\tname\n")
        for current_info in find_old_workflow_ids(
            orgreposlug,
            now - (job_life_clock * n_windows),
            now - job_midlife_warning,
            standard_headers
        ):
            if current_info["job_status"] == "age_warning":
                if not (ignore == ""):
                    jobs_we_care_about = filter_ignored_jobs(current_info, ignore, standard_headers)
                    if len(jobs_we_care_about) == 0:
                        print(f"ignoring workflow: {current_info['id']} See more info at https://app.circleci.com/pipelines/workflows/{current_info['id']}")
                        continue
                print(
                    f"midlife warning for workflow ({current_info['name']}), started by gh:{current_info['username']}. See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
            else:
                print(
                    f"found too old workflow: {current_info['id']} ({current_info['name']}) See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
                if commit:
                    http_post(
                        f"https://circleci.com/api/v2/workflow/{current_info['id']}/cancel", headers=standard_headers)

            f.write(
                f"{current_info['job_status']}\ttrue\t{current_info['id']}\t{current_info['username']}\t{current_info['name']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("circleapitoken",
                        help="the CircleCI API token for this script")
    parser.add_argument("orgreposlug",
                        help="the location, user-or-org/repository-name , of this repository")

    parser.add_argument("--output-file",
                        help="output to file path",
                        default="/tmp/notifications.tsv")
    parser.add_argument("--commit",
                        help="just cancel jobs",
                        default=False,
                        action="store_true")
    parser.add_argument("--n-windows",
                        help="Number of windows to look back across. Default window length is 2 hours.",
                        type=int,
                        default=6)
    parser.add_argument("--ignore", help="if all awaiting approval jobs in the pipeline contain this word, do not age warn about it", default="")

    args = parser.parse_args()

    main(args.circleapitoken, args.orgreposlug,
         args.n_windows, args.output_file, args.commit, args.ignore)
