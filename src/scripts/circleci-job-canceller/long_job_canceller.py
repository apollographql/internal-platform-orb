#!/usr/bin/env python3

from Modules.circle_utils import *
import requests
import datetime
import sys
import os.path

from dateutil.parser import *

import argparse

sys.path.append("..")  # added!


job_life_clock = datetime.timedelta(hours=2)
job_midlife_warning = datetime.timedelta(hours=1)

robot_committers = ["apollo-bot2"]


def get_workflow_started_by(current_workflow, headers):
    user_url = f"https://circleci.com/api/v2/user/{current_workflow['started_by']}"
    user_info = requests.get(user_url, headers=headers).json()
    # the Github / CircleCI scheduling bot won't have a username (JSON body will be {'message': 'Not found.'})
    username = user_info.get("login", "")

    return username


def find_old_workflow_ids(repo_slug, headers):
    utc_tz = datetime.timezone(datetime.timedelta(hours=0))
    now = datetime.datetime.now(utc_tz)

    for current_pipeline in get_all_items(f"/project/gh/{repo_slug}/pipeline", headers):
        for current_workflow in get_all_items(f"/pipeline/{current_pipeline['id']}/workflow", headers):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "circleapitoken", help="the CircleCI API token for this script")
    parser.add_argument(
        "orgreposlug", help="the location, user-or-org/repository-name , of this repository")

    parser.add_argument("--output-file", help="output to file path",
                        default="/tmp/notifications.tsv", )
    parser.add_argument("--just-do-it", help="just cancel jobs",
                        default=False, action="store_true")

    args = parser.parse_args()

    CIRCLE_API_KEY = args.circleapitoken
    cancel_jobs_here = args.just_do_it

    standard_headers = {"Circle-Token": args.circleapitoken}

    simple_path = os.path.abspath(os.path.expanduser(
        os.path.expandvars(args.output_file)))

    with open(simple_path, 'w') as f:
        f.write("job_status\tproceed\tid\tusername\tname\n")
        for current_info in find_old_workflow_ids(args.orgreposlug, standard_headers):
            if current_info["job_status"] == "age_warning":
                print(
                    f"midlife warning for workflow ({current_info['name']}), started by gh:{current_info['username']}. See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
            else:
                print(
                    f"found too old workflow: {current_info['id']} ({current_info['name']}) See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
                if cancel_jobs_here:
                    requests.post(
                        f"https://circleci.com/api/v2/workflow/{current_info['id']}/cancel", headers=standard_headers)

            f.write(
                f"{current_info['job_status']}\ttrue\t{current_info['id']}\t{current_info['username']}\t{current_info['name']}\n")
