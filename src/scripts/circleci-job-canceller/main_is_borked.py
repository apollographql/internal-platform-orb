#!/usr/bin/env python3

import requests

import argparse
import pprint
import json
import http
import datetime
import sys
from dateutil.parser import *

# Turn on / off debugging
#http.client.HTTPConnection.debuglevel = 1


oncall_subteam = "<!subteam^SFNQZTE4Q>"

leave_pending_jobs_for = datetime.timedelta(hours=1)

def make_graphql_query(githubtoken, orgreposlug):

    org_repo = orgreposlug.split("/")
    [org_name, repo_name] = org_repo

    # reduce dependencies by doing the GraphQL part myself
    # Play with this in Apollo Studio Explorer: https://tinyurl.com/4v7nsdmk
    graph_ql_query = {"query": """query($org_name: String!, $repo_name: String!) {
  viewer {
    organization(login: $org_name) {
      repository(name: $repo_name) {
        object(expression: "6eee88887f5736054c5749552250a5d77dfa6ed1") {
          ... on Commit {
            commitUrl
            status {
              state
              contexts {
                targetUrl
                createdAt
                state
                context
              }
            }
            author {
             user {
               login
             }
            }
          }
        }
      }
    }
  }
} """, "variables": {"org_name": org_name, "repo_name": repo_name} }

# potentially other interesting snippets
#            associatedPullRequests(first: 5) {
#              edges {
#                node {
#                  url      <-- returns the URL of the PR(s) associated with this commit
#                }
#              }
#            }

    graph_ql_verify = {"query": """query { viewer { login } }"""}

    res = requests.post("https://api.github.com/graphql", json=graph_ql_query, headers={
        "Authorization": f"Bearer {githubtoken}",
        "Content-Type": "application/json"
    })

    return res


def main(githubtoken, orgreposlug):
    now = datetime.datetime.now( datetime.timezone(datetime.timedelta(hours=0)) ) #datetime in UTC

    res = make_graphql_query(githubtoken, orgreposlug)

    commit_info = None

    if res.json().get("errors"):
        messages = []
        [messages.append(x.get('message')) for x in res.json().get("errors")]
        print(f"{oncall_subteam} an error was reported by the scheduled main commit checker. Message was {','.join(messages)}")
        sys.exit(1)

    try:
        commit_info = res.json().get("data").get("viewer").get("organization").get("repository").get("object")
    except AttributeError as e:
        print(e)
        pprint.pprint(res.json())
        raise e

    commit_state = commit_info.get("status").get("state")

    commit_url = commit_info.get("commitUrl")
    author = commit_info.get("author").get("user").get("login")

    if (commit_state == "PENDING"):
        # This is a slightly more targetted nudge than what log_job_canceller does as it's ONLY for head of main
        # (but _technically_ duplicated reminders)
        #
        # regardless main's HEAD commit spends most of its time here, experimentally
        pending_workflows = []
        [ pending_workflows.append(x) for x in commit_info.get("status").get("contexts") if ( ((x.get("state") == "PENDING") and ("ci/circleci" in x.get("context"))) and not("dev0" in x.get("context")))  ]
        # pending workflows targetting dev0 don't deserve a callout by themselves

        if ( len(pending_workflows) > 0 ):
            jobs_started_str = pending_workflows[0].get("createdAt")
            workflow_link = pending_workflows[0].get("targetUrl")   # will always be the same targetURL

            jobs_stated_dt = isoparse(jobs_started_str)

            if ( jobs_stated_dt < ( now - leave_pending_jobs_for ) ):
                print(f"Hey *gh:{author}*! Looks like your merge has spent some time in _staging_ to be tested. Go to *prod* :question: :link: <{workflow_link}|View on CircleCI>. - :heart: :canned_food:.")

    if (commit_state == "FAILURE"):
        print(f"Recent checks have found monorepo main is broken. Latest commit {commit_url} by gh:{author}. {oncall_subteam}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("githubapitoken", help="the Github API token for this script")
    # Token needs to have the following scopes:
    #   * admin:org read:org
    #   * repo repo:status

    parser.add_argument("orgreposlug", help="the location, user-or-org/repository-name , of this repository")

    args = parser.parse_args()

    main(args.githubapitoken, args.orgreposlug)
