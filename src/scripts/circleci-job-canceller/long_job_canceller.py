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
utc_tz = datetime.timezone(datetime.timedelta(hours=0))
now = datetime.datetime.now(utc_tz)

robot_committers = ["apollo-bot2"]


def get_workflow_started_by(current_workflow, headers):
    user_url = f"https://circleci.com/api/v2/user/{current_workflow['started_by']}"
    user_info = requests.get(user_url, headers=headers).json()
    # the Github / CircleCI scheduling bot won't have a username (JSON body will be {'message': 'Not found.'})
    username = user_info.get("login", "")

    return username


def find_old_workflow_ids(repo_slug, window_start, window_end, headers):
    print(f'Window to paginate through: [{window_start}, {window_end}]')
    for current_pipeline in get_all_items(f"/project/gh/{repo_slug}/pipeline", headers, None):
        # Paginate through only those pipelines which started inside our given window
        if str(window_end) < current_pipeline['created_at']:
            print(f'Pipeline too young: {current_pipeline["created_at"]}')
            continue
        if current_pipeline['created_at'] < str(window_start):
            print(f'Pipeline too old: {current_pipeline["created_at"]}')
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


def cancel_pipeline(pipeline, workflows):
    for workflow in workflows:
        if not workflow.get('stopped_at'):
            print(
                f'    Cancelling workflow: https://app.circleci.com/pipelines/{pipeline["project_slug"]}/{pipeline["number"]}/workflows/{workflow["id"]}')
            response = requests.post(
                f"https://circleci.com/api/v2/workflow/{current_info['id']}/cancel", headers=standard_headers)

            if not response['message'] == 'Accepted.':
                raise Exception(f'{response}')


def main(circleapitoken, orgreposlug, output_file, commit):
    standard_headers = {"Circle-Token": circleapitoken}

    simple_path = os.path.abspath(os.path.expanduser(
        os.path.expandvars(output_file)))

    with open(simple_path, 'w') as f:
        f.write("job_status\tproceed\tid\tusername\tname\n")
        for current_info in find_old_workflow_ids(
            orgreposlug,
            now - (job_life_clock * 5),
            now - job_midlife_warning,
            standard_headers
        ):
            if current_info["job_status"] == "age_warning":
                print(
                    f"midlife warning for workflow ({current_info['name']}), started by gh:{current_info['username']}. See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
            else:
                print(
                    f"found too old workflow: {current_info['id']} ({current_info['name']}) See more info at: https://app.circleci.com/pipelines/workflows/{current_info['id']}")
                if commit:
                    requests.post(
                        f"https://circleci.com/api/v2/workflow/{current_info['id']}/cancel", headers=standard_headers)

            f.write(
                f"{current_info['job_status']}\ttrue\t{current_info['id']}\t{current_info['username']}\t{current_info['name']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "circleapitoken", help="the CircleCI API token for this script")
    parser.add_argument(
        "orgreposlug", help="the location, user-or-org/repository-name , of this repository")

    parser.add_argument("--output-file", help="output to file path",
                        default="/tmp/notifications.tsv", )
    parser.add_argument("--commit", help="just cancel jobs",
                        default=False, action="store_true")

    args = parser.parse_args()

    main(args.circleapitoken, args.orgreposlug, args.output_file, args.commit)
