# -*- coding: utf-8 -*-
""" Chart submission with errors
    Partners or redhat associates submit charts which result in errors
"""
import os
import json
import base64
import pathlib
import logging
import shutil
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from string import Template

import git
import yaml
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
    parsers
)

from functional.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def secrets():
    @dataclass
    class Secret:
        test_repo: str
        bot_name: str
        bot_token: str
        
        base_branch: str
        pr_branch: str = ''
        pr_number: int = -1
        vendor_type: str = ''
        vendor: str = ''
        user: str = ''
        owners_file_content: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: null
users:
- githubUsername: ${bot_name}
vendor:
  label: ${vendor}
  name: ${vendor}
"""
        test_data_dir: str = 'tests/data/'
        #test_chart: str = 'tests/data/vault-0.13.0.tgz'
        #test_report: str = 'tests/data/report.yaml'
        #chart_name, chart_version = get_name_and_version_from_report(test_report)

    bot_name, bot_token = get_bot_name_and_token()

    test_repo = TEST_REPO
    repo = git.Repo()

    # Differentiate between github runner env and local env
    github_actions = os.environ.get("GITHUB_ACTIONS")
    if github_actions:
        # Create a new branch locally from detached HEAD
        head_sha = create_new_branch_locally(repo)

    push_current_branch_to_remote_test_repo(repo, test_repo, bot_token)

    base_branch = 'error-chart-' + get_active_branch_name(repo)

    secrets = Secret(test_repo, bot_name, bot_token, base_branch)
    yield secrets

    # Teardown step to cleanup branches
    repo.git.worktree('prune')

    if github_actions:
        logger.info(f"Delete remote '{head_sha}' branch")
        github_api(
            'delete', f'repos/{secrets.test_repo}/git/refs/heads/{head_sha}', secrets.bot_token)

    cleanup_branches(secrets, repo, logger)


@scenario('features/user_submits_chart_with_errors.feature', "An unauthorized user submits a chart with report")
def test_chart_submission_by_unauthorized_user():
    """An unauthorized user submits a chart with report"""

@given(parsers.parse("A <user> wants to submit a chart"))
def user_wants_to_submit_a_chart(secrets, user):
    """A user wants to submit a chart"""

    logger.info(f"User: {user}")
    secrets.user = user

@given(parsers.parse("<vendor> of <vendor_type> wants to submit <chart> of <version>"))
def vendor_of_vendor_type_wants_to_submit_chart_of_version(secrets, vendor, vendor_type, chart, version):
    """partner user is not present in the OWNERS file of the chart"""
    
    logger.info(f"Vendor: {vendor} Vendor Type: {vendor_type} Chart: {chart} Version: {version}")

    secrets.vendor_type = vendor_type
    secrets.vendor = get_unique_vendor(vendor)
    secrets.chart_name = chart
    secrets.chart_version = version

    #Substitude the values in owners file content
    values = {'bot_name': secrets.user, 'vendor': secrets.vendor, 'chart_name': secrets.chart_name}
    secrets.owners_file_content = Template(secrets.owners_file_content).substitute(values)


@given("the user creates a branch to add a new chart version")
def the_user_creates_a_branch_to_add_a_new_chart_version(secrets):
    """the user creates a branch to add a new chart version."""

    with TemporaryDirectory(prefix='tci-') as temp_dir:
        secrets.base_branch = f'{secrets.vendor_type}-{secrets.vendor}-{secrets.base_branch}'
        secrets.pr_branch = f'{secrets.base_branch}-pr'

        repo = git.Repo(os.getcwd())
        set_git_username_email(repo, secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        if os.environ.get('WORKFLOW_DEVELOPMENT'):
            logger.info("Wokflow development enabled")
            commit_current_changes(repo, commit_message='Checkpoint')

        # Make PR's from a temporary directory
        old_cwd = os.getcwd()
        logger.info(f'Worktree directory: {temp_dir}')
        repo.git.worktree('add', '--detach', temp_dir, f'HEAD')

        os.chdir(temp_dir)
        repo = git.Repo(temp_dir)
        set_git_username_email(repo, secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        repo.git.checkout('-b', secrets.base_branch)
        
        chart_dir = f'charts/{secrets.vendor_type}/{secrets.vendor}/{secrets.chart_name}'
        pathlib.Path(
            f'{chart_dir}/{secrets.chart_version}').mkdir(parents=True, exist_ok=True)

        # Remove chart files from base branch
        remove_chart_dir_from_base_branch(secrets, chart_dir, repo, logger)

        # Remove the OWNERS file from base branch
        remove_owners_file_from_base_branch(secrets, chart_dir, repo, logger)

        # Create the OWNERS file
        with open(f'{chart_dir}/OWNERS', 'w') as fd:
            fd.write(secrets.owners_file_content)
        
        # Push OWNERS file to the test_repo
        push_owners_file_to_base_branch(secrets, chart_dir, repo, logger)

        # Copy the chart tar into temporary directory for PR submission
        chart_tar_file = get_chart_tar_file_name(secrets)
        shutil.copyfile(f'{old_cwd}/{secrets.test_data_dir}{chart_tar_file}',
            f'{chart_dir}/{secrets.chart_version}/{chart_tar_file}')

        # Copy report to temporary location
        copy_report_to_tmp_location(secrets, chart_dir)

        # Push chart src files to test_repo:pr_branch
        push_chart_files_to_pr_branch(secrets, chart_dir, chart_tar_file, repo, logger)

        os.chdir(old_cwd)


@when("the user sends a pull request with chart and report")
def the_user_sends_a_pull_request_with_chart_and_report(secrets):
    """The user sends the pull request with the chart tar files."""
    data = {'head': secrets.pr_branch, 'base': secrets.base_branch,
            'title': secrets.pr_branch, 'body': os.environ.get('PR_BODY')}

    logger.info(
        f"Create PR with chart tar files from '{secrets.test_repo}:{secrets.pr_branch}'")
    r = github_api(
        'post', f'repos/{secrets.test_repo}/pulls', secrets.bot_token, json=data)
    j = json.loads(r.text)
    secrets.pr_number = j['number']


@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(secrets):
    """the pull request is not merged"""

    run_id = get_run_id(secrets)
    conclusion = get_run_result(secrets, run_id)

    if conclusion == 'failure':
        logger.info("Workflow run was 'failure' which is expected")
    else:
        pytest.fail(
            f"Workflow for the submitted PR success which is unexpected, run id: {run_id}")

    r = github_api(
        'get', f'repos/{secrets.test_repo}/pulls/{secrets.pr_number}/merge', secrets.bot_token)
    
    if r.status_code == 404:
        logger.info("PR not merged, which is expected")
    else:
        pytest.fail("PR merged, which is unexpected")

@then(parsers.parse("user gets the <message> with steps to follow for resolving the issue in the pull request"))
def user_gets_the_message_with_steps_to_follow_for_resolving_the_issue_in_the_pull_request(secrets, message):
    """user gets the message with steps to follow for resolving the issue in the pull request"""
    
    #https://docs.github.com/en/rest/guides/working-with-comments
    #curl -H "Accept: application/vnd.github.v3+json" https://api.github.com/repos/openshift-helm-charts/sandbox/issues/{pr_number}/comments

    r = github_api(
        'get', f'repos/{secrets.test_repo}/issues/{secrets.pr_number}/comments', secrets.bot_token)
    logger.info(f'STATUS_CODE: {r.status_code}')
    
    response = json.loads(r.text)
    complete_comment = response[0]['body']

    if message in complete_comment:
        logger.info("Found the expected comment in the PR")
    else:
        pytest.fail("Was expecting '{expected_string}' in the comment {complete_comment}")

    
    

