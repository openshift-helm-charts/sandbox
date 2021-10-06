# -*- coding: utf-8 -*-
""" Chart submitted by an unauthorized user
    Partners or redhat associates can not submit charts if they are not in the OWNERS file of the chart
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
        pr_branch: str

        pr_number: int = -1
        vendor_type: str = ''
        vendor: str = ''
        owners_file_content: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: null
users: []
vendor:
  label: ${vendor}
  name: ${vendor}
"""
        test_chart: str = 'tests/data/vault-0.13.0.tgz'
        test_report: str = 'tests/data/report.yaml'
        chart_name, chart_version = get_name_and_version_from_report(
            test_report)

    bot_name, bot_token = get_bot_name_and_token()

    test_repo = TEST_REPO
    repo = git.Repo()

    # Differentiate between github runner env and local env
    github_actions = os.environ.get("GITHUB_ACTIONS")
    if github_actions:
        # Create a new branch locally from detached HEAD
        head_sha = repo.git.rev_parse('--short', 'HEAD')
        local_branches = [h.name for h in repo.heads]
        if head_sha not in local_branches:
            repo.git.checkout('-b', f'{head_sha}')

    current_branch = repo.active_branch.name
    r = github_api(
        'get', f'repos/{test_repo}/branches', bot_token)
    branches = json.loads(r.text)
    branch_names = [branch['name'] for branch in branches]
    if current_branch not in branch_names:
        logger.info(
            f"{test_repo}:{current_branch} does not exists, creating with local branch")
    repo.git.push(f'https://x-access-token:{bot_token}@github.com/{test_repo}',
                  f'HEAD:refs/heads/{current_branch}', '-f')

    base_branch = f'chart-tar-with-report-{current_branch}'
    pr_branch = base_branch + '-pr'

    secrets = Secret(test_repo, bot_name, bot_token, base_branch, pr_branch)
    yield secrets

    # Teardown step to cleanup branches
    repo.git.worktree('prune')

    if github_actions:
        logger.info(f"Delete remote '{head_sha}' branch")
        github_api(
            'delete', f'repos/{secrets.test_repo}/git/refs/heads/{head_sha}', secrets.bot_token)

    logger.info(f"Delete '{secrets.test_repo}:{secrets.base_branch}'")
    github_api(
        'delete', f'repos/{secrets.test_repo}/git/refs/heads/{secrets.base_branch}', secrets.bot_token)

    logger.info(f"Delete '{secrets.test_repo}:{secrets.base_branch}-gh-pages'")
    github_api(
        'delete', f'repos/{secrets.test_repo}/git/refs/heads/{secrets.base_branch}-gh-pages', secrets.bot_token)

    logger.info(f"Delete '{secrets.test_repo}:{secrets.pr_branch}'")
    github_api(
        'delete', f'repos/{secrets.test_repo}/git/refs/heads/{secrets.pr_branch}', secrets.bot_token)

    logger.info(f"Delete local '{secrets.base_branch}'")
    try:
        repo.git.branch('-D', secrets.base_branch)
    except git.exc.GitCommandError:
        logger.info(f"Local '{secrets.base_branch}' does not exist")


@scenario('features/chart_submitted_by_unauthorized_user.feature', "An unauthorized partner user submits a chart with report")
def test_partner_chart_submission_by_unauthorized_user():
    """An unauthorized partner user submits a chart with report"""

@given("partner user is not present in the OWNERS file of the chart")
def partner_user_not_present_in_the_chart_owners_file(secrets):
    """partner user is not present in the OWNERS file of the chart"""
    secrets.vendor_type = 'partners'
    secrets.vendor = get_unique_vendor('hashicorp')

@given("the user creates a branch to add a new chart version")
def the_user_has_created_a_error_free_chart_tar_with_report(secrets):
    """the user creates a branch to add a new chart version."""

    with TemporaryDirectory(prefix='tci-') as temp_dir:
        secrets.base_branch = f'{secrets.vendor_type}-{secrets.vendor}-{secrets.base_branch}'
        secrets.pr_branch = f'{secrets.base_branch}-pr'

        repo = git.Repo(os.getcwd())
        set_git_username_email(repo, secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        if os.environ.get('WORKFLOW_DEVELOPMENT'):
            logger.info("Wokflow development enabled")
            repo.git.add(A=True)
            repo.git.commit('-m', 'Checkpoint')

        # Get SHA from 'dev-gh-pages' branch
        logger.info(
            f"Create '{secrets.test_repo}:{secrets.base_branch}-gh-pages' from '{secrets.test_repo}:dev-gh-pages'")
        r = github_api(
            'get', f'repos/{secrets.test_repo}/git/ref/heads/dev-gh-pages', secrets.bot_token)
        j = json.loads(r.text)
        sha = j['object']['sha']

        # Create a new gh-pages branch for testing
        data = {'ref': f'refs/heads/{secrets.base_branch}-gh-pages', 'sha': sha}
        r = github_api(
            'post', f'repos/{secrets.test_repo}/git/refs', secrets.bot_token, json=data)

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
        logger.info(
            f"Remove {chart_dir}/{secrets.chart_version} from {secrets.test_repo}:{secrets.base_branch}")
        try:
            repo.git.rm('-rf', '--cached', f'{chart_dir}/{secrets.chart_version}')
            repo.git.commit(
                '-m', f'Remove {chart_dir}/{secrets.chart_version}')
            repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                            f'HEAD:refs/heads/{secrets.base_branch}')
        except git.exc.GitCommandError:
            logger.info(
                f"{chart_dir}/{secrets.chart_version} not exist on {secrets.test_repo}:{secrets.base_branch}")

        # Remove the OWNERS file from base branch
        logger.info(
            f"Remove {chart_dir}/OWNERS from {secrets.test_repo}:{secrets.base_branch}")
        try:
            repo.git.rm('-rf', '--cached', f'{chart_dir}/OWNERS')
            repo.git.commit(
                '-m', f'Remove {chart_dir}/OWNERS')
            repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                            f'HEAD:refs/heads/{secrets.base_branch}')
        except git.exc.GitCommandError:
            logger.info(
                f"{chart_dir}/OWNERS not exist on {secrets.test_repo}:{secrets.base_branch}")

        # Create the OWNERS file from the string template
        values = {'bot_name': secrets.bot_name,
                  'vendor': secrets.vendor, 'chart_name': secrets.chart_name}
        content = Template(secrets.owners_file_content).substitute(values)
        with open(f'{chart_dir}/OWNERS', 'w') as fd:
            fd.write(content)

        # Push OWNERS file to the test_repo
        logger.info(
            f"Push OWNERS file to '{secrets.test_repo}:{secrets.base_branch}'")
        repo.git.add(f'{chart_dir}/OWNERS')
        repo.git.commit(
            '-m', f"Add {secrets.vendor} {secrets.chart_name} OWNERS file")
        repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                      f'HEAD:refs/heads/{secrets.base_branch}', '-f')

        # Copy the chart tar into temporary directory for PR submission
        logger.info(
            f"Push report and chart tar to '{secrets.test_repo}:{secrets.pr_branch}'")
        chart_tar = secrets.test_chart.split('/')[-1]
        shutil.copyfile(f'{old_cwd}/{secrets.test_chart}',
                        f'{chart_dir}/{secrets.chart_version}/{chart_tar}')

        # Copy report to temporary location and push to test_repo:pr_branch
        tmpl = open(secrets.test_report).read()
        values = {'repository': secrets.test_repo,
                  'branch': secrets.base_branch}
        content = Template(tmpl).substitute(values)
        with open(f'{chart_dir}/{secrets.chart_version}/report.yaml', 'w') as fd:
            fd.write(content)

        # Push chart src files to test_repo:pr_branch
        repo.git.add(f'{chart_dir}/{secrets.chart_version}/report.yaml')
        repo.git.add(f'{chart_dir}/{secrets.chart_version}/{chart_tar}')
        repo.git.commit(
            '-m', f"Add {secrets.vendor} {secrets.chart_name} {secrets.chart_version} chart tar files and report")

        repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
                      f'HEAD:refs/heads/{secrets.pr_branch}', '-f')

        os.chdir(old_cwd)


@when("the user sends a pull request with chart and report")
def the_user_sends_the_pull_request(secrets):
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

@then("user gets the message with steps to follow for resolving the issue in the pull request")
def user_gets_the_message_with_steps_to_follow_in_the_pull_request(secrets):
    """user gets the message with steps to follow for resolving the issue in the pull request"""
    
    #https://docs.github.com/en/rest/guides/working-with-comments
    #curl -H "Accept: application/vnd.github.v3+json" https://api.github.com/repos/openshift-helm-charts/sandbox/issues/{pr_number}/comments
    #[ERROR]  tisutisu is not allowed to submit the chart on behalf of hashicorp-1633505743

    r = github_api(
        'get', f'repos/{secrets.test_repo}/issues/{secrets.pr_number}/comments', secrets.bot_token)
    response = json.loads(r.text)

    complete_comment = response[0]['body']
    expected_string = f"{secrets.bot_name} is not allowed to submit the chart on behalf of {secrets.vendor}"

    if expected_string in complete_comment:
        logger.info("Found the expected comment in the PR")
    else:
        pytest.fail("Expected comment not found in the PR")

    
    

