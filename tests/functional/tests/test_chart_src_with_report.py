# -*- coding: utf-8 -*-
"""Report and chart source submission

Partners or redhat associates can publish their chart by submitting
error-free chart in source format with the report.
"""
import os
import json
import base64
import pathlib
import shutil
import tarfile
import logging
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

from functional.utils.utils import *
from functional.utils.secret import OneShotTestingSecret, SecretOneShotTesting
from functional.utils.certification_workflow_test import CertificationWorkflowTestOneShot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def secrets():
    owners_file_content = """\
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
    test_chart = 'tests/data/vault-0.13.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = CertificationWorkflowTestOneShot(owners_file_content, test_chart, test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('features/report_and_chart_src.feature', "The partner hashicorp submits an error-free chart source with report for vault")
def test_partner_chart_src_submission():
    """The partner hashicorp submits an error-free chart source with report for vault."""


@scenario('features/report_and_chart_src.feature', "A redhat associate submits an error-free chart source with report for vault")
def test_redhat_chart_src_submission():
    """A redhat associate submits an error-free chart source with report for vault."""


@given("hashicorp is a valid partner")
def hashicorp_is_a_valid_partner(secrets):
    """hashicorp is a valid partner"""
    secrets.set_vendor(get_unique_vendor('hashicorp'), 'partners')


@given("a redhat associate has a valid identity")
def redhat_associate_is_valid(secrets):
    """a redhat associate has a valid identity"""
    secrets.set_vendor(get_unique_vendor('redhat'), 'redhat')


@given("hashicorp has created an error-free chart source and report for vault")
@given("the redhat associate has created an error-free chart source and report for vault")
def the_user_has_created_a_error_free_chart_src_with_report(secrets):
    """The user has created an error-free chart source."""

    secrets.setup_git_context()
    secrets.setup_gh_pages_branch()
    secrets.cleanup_temp_dir()
    secrets.process_owners_file()
    secrets.process_chart(is_tarball=False)
    secrets.process_report()
    secrets.push_chart()

    # with TemporaryDirectory(prefix='tci-') as temp_dir:
        # secrets.base_branch = f'{secrets.vendor_type}-{secrets.vendor}-{secrets.base_branch}'
        # secrets.pr_branch = f'{secrets.base_branch}-pr'

        # repo = git.Repo(os.getcwd())
        # set_git_username_email(repo, secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        # if os.environ.get('WORKFLOW_DEVELOPMENT'):
        #     logger.info("Wokflow development enabled")
        #     repo.git.add(A=True)
        #     repo.git.commit('-m', 'Checkpoint')

        # # Get SHA from 'dev-gh-pages' branch
        # logger.info(
        #     f"Create '{secrets.test_repo}:{secrets.base_branch}-gh-pages' from '{secrets.test_repo}:dev-gh-pages'")
        # r = github_api(
        #     'get', f'repos/{secrets.test_repo}/git/ref/heads/dev-gh-pages', secrets.bot_token)
        # j = json.loads(r.text)
        # sha = j['object']['sha']

        # # Create a new gh-pages branch for testing
        # data = {'ref': f'refs/heads/{secrets.base_branch}-gh-pages', 'sha': sha}
        # r = github_api(
        #     'post', f'repos/{secrets.test_repo}/git/refs', secrets.bot_token, json=data)

        # # Make PR's from a temporary directory
        # old_cwd = os.getcwd()
        # logger.info(f'Worktree directory: {temp_dir}')
        # repo.git.worktree('add', '--detach', temp_dir, f'HEAD')

        # os.chdir(temp_dir)
        # repo = git.Repo(temp_dir)
        # set_git_username_email(repo, secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        # repo.git.checkout('-b', secrets.base_branch)
        # chart_dir = f'charts/{secrets.vendor_type}/{secrets.vendor}/{secrets.chart_name}'
        # pathlib.Path(
        #     f'{chart_dir}/{secrets.chart_version}').mkdir(parents=True, exist_ok=True)

        # # Remove chart files from base branch
        # logger.info(
        #     f"Remove {chart_dir}/{secrets.chart_version} from {secrets.test_repo}:{secrets.base_branch}")
        # try:
        #     repo.git.rm('-rf', '--cached', f'{chart_dir}/{secrets.chart_version}')
        #     repo.git.commit(
        #         '-m', f'Remove {chart_dir}/{secrets.chart_version}')
        #     repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
        #                     f'HEAD:refs/heads/{secrets.base_branch}')
        # except git.exc.GitCommandError:
        #     logger.info(
        #         f"{chart_dir}/{secrets.chart_version} not exist on {secrets.test_repo}:{secrets.base_branch}")

        # # Remove the OWNERS file from base branch
        # logger.info(
        #     f"Remove {chart_dir}/OWNERS from {secrets.test_repo}:{secrets.base_branch}")
        # try:
        #     repo.git.rm('-rf', '--cached', f'{chart_dir}/OWNERS')
        #     repo.git.commit(
        #         '-m', f'Remove {chart_dir}/OWNERS')
        #     repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
        #                     f'HEAD:refs/heads/{secrets.base_branch}')
        # except git.exc.GitCommandError:
        #     logger.info(
        #         f"{chart_dir}/OWNERS not exist on {secrets.test_repo}:{secrets.base_branch}")

        # # Create the OWNERS file from the string template
        # values = {'bot_name': secrets.bot_name,
        #           'vendor': secrets.vendor, 'chart_name': secrets.chart_name}
        # content = Template(secrets.owners_file_content).substitute(values)
        # with open(f'{chart_dir}/OWNERS', 'w') as fd:
        #     fd.write(content)

        # # Push OWNERS file to the test_repo
        # logger.info(
        #     f"Push OWNERS file to '{secrets.test_repo}:{secrets.base_branch}'")
        # repo.git.add(f'{chart_dir}/OWNERS')
        # repo.git.commit(
        #     '-m', f"Add {secrets.vendor} {secrets.chart_name} OWNERS file")
        # repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
        #               f'HEAD:refs/heads/{secrets.base_branch}', '-f')

        # # Unzip files into temporary directory for PR submission
        # extract_chart_tgz(secrets.test_chart, f'{chart_dir}/{secrets.chart_version}', secrets, logger)

        # # Copy report to temporary location and push to test_repo:pr_branch
        # logger.info(
        #     f"Push report to '{secrets.test_repo}:{secrets.pr_branch}'")
        # tmpl = open(secrets.test_report).read()
        # values = {'repository': secrets.test_repo,
        #           'branch': secrets.base_branch}
        # content = Template(tmpl).substitute(values)
        # with open(f'{chart_dir}/{secrets.chart_version}/report.yaml', 'w') as fd:
        #     fd.write(content)

        # # Push chart src files to test_repo:pr_branch
        # repo.git.add(f'{chart_dir}/{secrets.chart_version}/src')
        # repo.git.add(f'{chart_dir}/{secrets.chart_version}/report.yaml')
        # repo.git.commit(
        #     '-m', f"Add {secrets.vendor} {secrets.chart_name} {secrets.chart_version} chart source files and report")

        # repo.git.push(f'https://x-access-token:{secrets.bot_token}@github.com/{secrets.test_repo}',
        #               f'HEAD:refs/heads/{secrets.pr_branch}', '-f')

        # os.chdir(old_cwd)


@when("hashicorp sends a pull request with the vault source chart and report")
@when("the redhat associate sends a pull request with the vault source chart and report")
def the_user_sends_the_pull_request(secrets):
    """The user sends the pull request with the chart source files."""
    # data = {'head': secrets.pr_branch, 'base': secrets.base_branch,
    #         'title': secrets.pr_branch, 'body': os.environ.get('PR_BODY')}

    # logger.info(
    #     f"Create PR with chart source files from '{secrets.test_repo}:{secrets.pr_branch}'")
    # r = github_api(
    #     'post', f'repos/{secrets.test_repo}/pulls', secrets.bot_token, json=data)
    # j = json.loads(r.text)
    # secrets.pr_number = j['number']
    secrets.send_pull_request()

@then("hashicorp sees the pull request is merged")
@then("the redhat associate sees the pull request is merged")
def the_user_should_see_the_pull_request_getting_merged(secrets):
    """The user should see the pull request getting merged."""

    # run_id = get_run_id(secrets)
    # conclusion = get_run_result(secrets, run_id)
    # if conclusion == 'success':
    #     logger.info("Workflow run was 'success'")
    # else:
    #     pytest.fail(
    #         f"Workflow for the submitted PR did not success, run id: {run_id}")

    # r = github_api(
    #     'get', f'repos/{secrets.test_repo}/pulls/{secrets.pr_number}/merge', secrets.bot_token)
    # if r.status_code == 204:
    #     logger.info("PR merged sucessfully")
    # else:
    #     pytest.fail("Workflow for submitted PR success but PR not merged")
    secrets.check_workflow_conclusion()
    secrets.check_pull_request_result()


@then("the index.yaml file is updated with an entry for the submitted chart")
def the_index_yaml_is_updated_with_a_new_entry(secrets):
    """The index.yaml file is updated with a new entry."""

    # repo = git.Repo(os.getcwd())
    # old_branch = repo.active_branch.name
    # repo.git.fetch(f'https://github.com/{secrets.test_repo}.git',
    #                '{0}:{0}'.format(f'{secrets.base_branch}-gh-pages'), '-f')
    # repo.git.checkout(f'{secrets.base_branch}-gh-pages')
    # with open('index.yaml', 'r') as fd:
    #     try:
    #         index = yaml.safe_load(fd)
    #     except yaml.YAMLError as err:
    #         pytest.fail(f"error parsing index.yaml: {err}")

    # entry = secrets.vendor + '-' + secrets.chart_name
    # if entry not in index['entries']:
    #     pytest.fail(
    #         f"{secrets.chart_name} {secrets.chart_version} not added to index")

    # version_list = [release['version'] for release in index['entries'][entry]]
    # if secrets.chart_version not in version_list:
    #     pytest.fail(
    #         f"{secrets.chart_name} {secrets.chart_version} not added to index")

    # logger.info("Index updated correctly, cleaning up local branch")
    # repo.git.checkout(old_branch)
    # repo.git.branch('-D', f'{secrets.base_branch}-gh-pages')
    secrets.check_index_yaml()


@then("a release for the vault chart is published with corresponding report and chart tarball")
def the_release_is_published(secrets):
    """a release is published with the chart"""

    # expected_tag = f'{secrets.vendor}-{secrets.chart_name}-{secrets.chart_version}'
    # try:
    #     release = get_release_by_tag(secrets, expected_tag)
    #     logger.info(f"Released '{expected_tag}' successfully")

    #     chart_tgz = secrets.test_chart.split('/')[-1]
    #     expected_chart_asset = f'{secrets.vendor}-{chart_tgz}'
    #     required_assets = [expected_chart_asset]
    #     logger.info(f"Check '{required_assets}' is in release assets")
    #     release_id = release['id']
    #     get_release_assets(secrets, release_id, required_assets)
    #     return
    # finally:
    #     logger.info(f"Delete release '{expected_tag}'")
    #     github_api(
    #         'delete', f'repos/{secrets.test_repo}/releases/{release_id}', secrets.bot_token)

    #     logger.info(f"Delete release tag '{expected_tag}'")
    #     github_api(
    #         'delete', f'repos/{secrets.test_repo}/git/refs/tags/{expected_tag}', secrets.bot_token)
    secrets.check_release_result()
