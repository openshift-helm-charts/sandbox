
import argparse
import itertools
import logging
import requests
import sys
import analytics
import os
from github import Github

sys.path.append('../')
from indexfile import index

import prepare_pr_comment as pr_comment

logging.basicConfig(level=logging.INFO)

def parse_response(response):
    result = []
    for obj in response:
        if 'name' in obj and 'assets' in obj:
            for asset in obj['assets']:
                if asset["name"].endswith(".tgz"):
                    release = { 'name' : obj['name'], "asset" : { asset.get('name') : asset.get('download_count', 0)}}
                    result.append(release)
    return result


def get_release_metrics():
    result = []
    for i in itertools.count(start=1):
        response = requests.get(
            f'https://api.github.com/repos/openshift-helm-charts/charts/releases?per_page=100&page={i}')
        if not 200 <= response.status_code < 300:
            logging.error(f"unexpected response getting release data : {response.status_code} : {response.reason}")
            sys.exit(1)
        response_json = response.json()
        if len(response_json) == 0:
            break
        result.extend(response_json)
    return parse_response(result)

def send_release_metrics(write_key, downloads):
    metrics={}
    for release in downloads:
        _,provider,chart,_ = index.get_chart_info(release.get('name'))
        if len(provider)>0:
            if provider not in metrics:
                metrics[provider] = {}
            if chart not in metrics[provider]:
                metrics[provider][chart] = {}

            for key in release.get('asset'):
                metrics[provider][chart][key] = release.get('asset')[key]


    for provider in metrics:
        for chart in metrics[provider]:
            send_metric(write_key,provider,f"{chart} downloads", metrics[provider][chart])

def process_report_fails(message):

    fails = ""
    num_error_messages = 0
    error_messages = []
    checks_failed = []
    message_lines = message.split("\n")
    for message_line in message_lines:
        message_line = message_line.strip()
        if fails:
            if "Error message(s)" in message_line:
                num_error_messages = 1
            elif num_error_messages <= int(fails):
                logging.info(f"[INFO] add error message: {message_line.strip()}" )
                error_messages.append(message_line.strip())
                num_error_messages +=1
            else:
                break
        elif "Number of checks failed" in message_line:
            body_line_parts = message_line.split(":")
            fails = body_line_parts[1].strip()
            logging.info(f"Number of failures in report {fails}")

    for error_message in error_messages:
        if ("Missing required annotations" in error_message
                or
                "Empty metadata in chart" in error_messages
        ):
            checks_failed.append("required-annotations-present")
        elif "Chart test files do not exist" in error_message:
            checks_failed.append("required-annotations-present")
        elif "Chart test files do not exist" in error_message:
            checks_failed.append("contains-test")
        elif "API version is not V2, used in Helm 3" in error_message:
            checks_failed.append("is-helm-v3")
        elif "Values file does not exist" in error_message:
            checks_failed.append("contains-values")
        elif "Values schema file does not exist" in error_message:
            checks_failed.append("contains-values-schema")
        elif ("Kubernetes version is not specified" in error_message
              or
              "Error converting kubeVersion to an OCP range" in error_message
        ):
            checks_failed.append("has-kubeversion")
        elif "Helm lint has failed" in error_message:
            checks_failed.append("helm_lint")
        elif ( "Failed to certify images" in error_message
               or
               "Image is not Red Hat certified" in error_message
        ):
            if "images-are-certified" not in checks_failed:
                checks_failed.append("images-are-certified")
        elif "Chart does not have a README" in error_message:
            checks_failed.append("has-readme")
        elif "Missing mandatory check" in error_messages:
            checks_failed.append("missing-mandatory-check")
        elif "Chart contains CRDs" in error_messages:
            checks_failed.append("not-contains-crds")
        elif "CSI objects exist" in error_message:
            checks_failed.append("not-contain-csi-objects")
        else:
            checks_failed.append("chart-testing")

    return int(fails),checks_failed

def process_comments(repo,pr):

    issue = repo.get_issue(number=pr.number)
    comments = issue.get_comments()
    num_builds = 0
    for comment in comments:
        report_result = parse_message(comment,pr.number)
        if report_result != "not-found":
            num_builds += 1

    return num_builds

def parse_message(message,pr_number):
    report_result = "not-found"
    if pr_comment.get_comment_header(pr_number) in message:
        if pr_comment.get_verifier_errors_comment() in message:
            report_result = "report-failure"
        elif pr_comment.get_content_failure_message() in message:
            report_result = "content-failure"
        elif pr_comment.get_success_coment() in message:
            report_result = "report-pass"
        elif pr_comment.get_community_review_message() in message:
            report_result = "community_review"

    return report_result

def get_pr_content(pr):

    pattern = re.compile(r"charts/([\w-]+)/([\w-]+)/([\w\.-]+)/([\w\.-]+)/.*")
    commits=pr.get_commits()

    # get the files in the PR
    pr_chart_submission_files = []
    for commit in commits:
        logging.info(f"    commit: {commit.url}")
        logging.info(f"    commit parents: {len(commit.parents)}")
        if len(commit.parents) < 2:
            files = commit.files
            for file in files:
                logging.info(f"      file: {file.filename}")
                logging.info(f"      file status: {file.status}")
                if pattern.match(file.filename):
                    if file.status != "removed" and not file.filename in pr_chart_submission_files:
                        pr_chart_submission_files.append(file.filename)
                    elif file.status == "removed" and file.filename in pr_chart_submission_files:
                        pr_chart_submission_files.remove(file.filename)
                else:
                    logging.info(f'ignore non chart file : {file.filename}')

    pr_content = "not-chart"
    if len(pr_chart_submission_files) > 0:
        logging.info(f"    Found unique files: {len(pr_chart_submission_files)}")
        match = pattern.match(pr_chart_submission_files[0])
        type,org,chart,version = match.groups()
        if type == "partners":
            type = "partner"
        logging.info(f"    type: {type},org: {org},chart: {chart},version: {version}")
        tgz_found = False
        report_found = False
        src_found = False
        for file in pr_chart_submission_files:
            filename = os.path.basename(file)
            if filename == "report.yaml":
                report_found = True
            elif filename.endswith(".tgz"):
                tgz_found = True
            elif filename == "Chart.yaml" and len(pr_chart_submission_files) > 2:
                src_found = True

        if report_found:
            if tgz_found:
                pr_content = "report and tgz"
            elif src_found:
                pr_content = "src and report"
            else:
                pr_content = "report only"
        elif tgz_found:
            pr_content = "tgz only"
        elif src_found:
            pr_content = "src only"

        return pr_content,type,org,chart,version

    return pr_content,"","","",""

def check_pr(pr):
    
    ignore_users=["zonggen","mmulholla","dperaza4dustbit","openshift-helm-charts-bot","baijum","tisutisu"]

    if pr.user_login in ignore_users or pr.draft or pr.base.ref != "main":
        logging.info(f"Ignore pr, user: {pr.user_login}, draft: {pr.draft}, target_branch: {pr.base.ref}")
        return "not-chart","","","",""

    return get_pr_content(pr)
    

def process_pr(write_key,message,pr_number,action):

    g = Github(os.environ.get("GITHUB_TOKEN"))
    repo = g.get_repo("openshift-helm-charts/charts")
    pr = repo.get_pull(pr_number)

    pr_content,type,provider,chart,version = check_pr(pr)
    if pr_content != "not-chart":
        if action == "opened":
            send_submission_metric(write_key,type,provider,chart,pr_number,pr_content)

        pr_result = parse_message(message,pr_number)
        num_fails=0
        if pr_result == "report-failure":
            num_fails,checks_failed = process_report_fails(message)
            for check in checks_failed:
                send_check_metric(write_key,type,provider,chart,pr_number,check)
        elif pr_result == "content-failure":
            num_fails = 1
        send_outcome_metric(write_key,type,provider,chart,pr_result,num_fails)

        ## if pr is merged we can collect summary stats
        if pr.merged_at:

            builds =  process_comments(repo,pr)
            logging.info(f"    PR  build cycles : {builds}")
            builds_out = str(builds)
            if builds > 5:
                builds_out = "> 5"

            elapsed_time = pr.merged_at - pr.created_at
            # round up to an hour to avoid 0 time
            elapsed_hours = elapsed_time.total_seconds()//3600
            duration = "0-1 hours"
            if 24 > elapsed_hours > 1:
                duration = "1-24 hours"
            elif 168 > elapsed_hours > 24:
                duration = "1-7 days"
            elif elapsed_hours > 168:
                duration= "> 7 days"

            send_merge_metric(write_key,type,provider,chart,duration,pr_number,builds_out,pr_content)


def send_outcome_metric(write_key,type,provider,chart,outcome,num_fails):

    properties = { "type": type, "provider": provider, "chart" : chart, "outcome" : outcome, "failures" :  num_fails}
    id = f"helm-metric-{provider}"

    send_metric(write_key,id,"PR-outcome",properties)


def send_check_metric(write_key,type,partner,chart,pr_number,check):

    properties = { "type": type, "provider": partner, "chart" : chart, "pr" : pr_number, "check" : check }
    id = f"helm-metric-{partner}"

    send_metric(write_key,id,"PR-checks",properties)

def send_merge_metric(write_key,type,partner,chart,duration,pr_number,num_builds,pr_content):

    id = f"helm-metric-{partner}"
    properties = { "type" : type, "provider": partner, "chart" : chart, "pr" : pr_number, "builds" :num_builds, "duration" : duration, "content" : pr_content}

    send_metric(write_key,id,"PR Merged",properties)

def send_submission_metric(write_key,type,partner,chart,pr_number,pr_content):

    id = f"helm-metric-{partner}"
    properties = { "type" : type, "provider": partner, "chart" : chart, "pr" : pr_number, "pr content": pr_content}

    send_metric(write_key,id,"PR Submission",properties)

def on_error(error,items):
    logging.info("An error occurred creating metrics:", error)
    logging.info("error with items:",items)
    sys.exit(1)


def send_metric(write_key,id,event,properties):

    analytics.write_key = write_key
    analytics.on_error = on_error

    logging.info(f'Add track:  id: {id},  event:{event},  properties:{properties}')

    #analytics.track(id, event, properties)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--write-key", dest="write_key", type=str, required=True,
                        help="segment write key")
    parser.add_argument("-t", "--metric-type", dest="type", type=str, required=True,
                        help="metric type, releases or pull_request")
    parser.add_argument("-m", "--message", dest="message", type=str, required=False,
                        help="message for metric")
    parser.add_argument("-e", "----event", dest="event", type=str, required=False,
                        help="github event")
    args = parser.parse_args()

    if not args.write_key:
        logging.info("Error: Segment write key not set")
        sys.exit(1)

    if args.type == "pull_request":
        process_pr(args.write_key,args.message,args.event.number,args.event.action)
    else:
        send_release_metrics(args.write_key,get_release_metrics())


if __name__ == '__main__':
    main()
