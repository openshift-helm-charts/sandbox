"""Utility class for setting up and manipulating certification workflow tests."""

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
from pathlib import Path

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
from functional.utils.secret import *
from functional.utils.set_directory import SetDirectory

@dataclass
class CertificationWorkflowTest:
    test_chart: str = ''
    test_report: str = ''
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
    chart_dir: str = ''
    secrets: SecretOneShotTesting = SecretOneShotTesting()
    temp_dir: TemporaryDirectory = None
    temp_repo: git.Repo = None


@dataclass
class CertificationWorkflowTestOneShot(CertificationWorkflowTest):
    old_cwd: str = os.getcwd()
    repo: git.Repo = git.Repo()
    github_actions: str = os.environ.get("GITHUB_ACTIONS")

    def __post_init__(self) -> None:
        if self.test_report:
            chart_name, chart_version = get_name_and_version_from_report(self.test_report)
        else:
            chart_name, chart_version = get_name_and_version_from_chart_tar(self.test_chart)
        bot_name, bot_token = get_bot_name_and_token()
        test_repo = TEST_REPO

        # Differentiate between github runner env and local env
        if self.github_actions:
            # Create a new branch locally from detached HEAD
            head_sha = self.repo.git.rev_parse('--short', 'HEAD')
            local_branches = [h.name for h in self.repo.heads]
            if head_sha not in local_branches:
                self.repo.git.checkout('-b', f'{head_sha}')

        current_branch = self.repo.active_branch.name
        r = github_api(
            'get', f'repos/{test_repo}/branches', bot_token)
        branches = json.loads(r.text)
        branch_names = [branch['name'] for branch in branches]
        if current_branch not in branch_names:
            logging.info(
                f"{test_repo}:{current_branch} does not exists, creating with local branch")
        self.repo.git.push(f'https://x-access-token:{bot_token}@github.com/{test_repo}',
                    f'HEAD:refs/heads/{current_branch}', '-f')

        base_branch = f'chart-src-with{"out" if not self.test_report else ""}-report-{current_branch}'
        pr_branch = base_branch + '-pr'

        self.secrets.owners_file_content = self.owners_file_content
        self.secrets.test_chart = self.test_chart
        self.secrets.test_report = self.test_report
        self.secrets.test_repo = test_repo
        self.secrets.bot_name = bot_name
        self.secrets.bot_token = bot_token
        self.secrets.base_branch = base_branch
        self.secrets.pr_branch = pr_branch
        self.secrets.chart_name = chart_name
        self.secrets.chart_version = chart_version

    def cleanup (self):
        # Teardown step to cleanup branches
        self.temp_dir.cleanup()
        self.repo.git.worktree('prune')

        if self.github_actions:
            head_sha = self.repo.git.rev_parse('--short', 'HEAD')
            logging.info(f"Delete remote '{head_sha}' branch")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{head_sha}', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.base_branch}'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.base_branch}', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.base_branch}-gh-pages'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.base_branch}-gh-pages', self.secrets.bot_token)

        logging.info(f"Delete '{self.secrets.test_repo}:{self.secrets.pr_branch}'")
        github_api(
            'delete', f'repos/{self.secrets.test_repo}/git/refs/heads/{self.secrets.pr_branch}', self.secrets.bot_token)

        logging.info(f"Delete local '{self.secrets.base_branch}'")
        try:
            self.repo.git.branch('-D', self.secrets.base_branch)
        except git.exc.GitCommandError:
            logging.info(f"Local '{self.secrets.base_branch}' does not exist")

    def set_vendor(self, vendor, vendor_type):
        self.secrets.vendor = vendor
        self.secrets.vendor_type = vendor_type
        self.secrets.base_branch = f'{self.secrets.vendor_type}-{self.secrets.vendor}-{self.secrets.base_branch}'
        self.secrets.pr_branch = f'{self.secrets.base_branch}-pr'
        self.chart_dir = f'charts/{self.secrets.vendor_type}/{self.secrets.vendor}/{self.secrets.chart_name}'

    def setup_git_context(self):
        set_git_username_email(self.repo, self.secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
        if os.environ.get('WORKFLOW_DEVELOPMENT'):
            logging.info("Wokflow development enabled")
            self.repo.git.add(A=True)
            self.repo.git.commit('-m', 'Checkpoint')

    def setup_gh_pages_branch(self):
        # Get SHA from 'dev-gh-pages' branch
        logging.info(
            f"Create '{self.secrets.test_repo}:{self.secrets.base_branch}-gh-pages' from '{self.secrets.test_repo}:dev-gh-pages'")
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/git/ref/heads/dev-gh-pages', self.secrets.bot_token)
        j = json.loads(r.text)
        sha = j['object']['sha']

        # Create a new gh-pages branch for testing
        data = {'ref': f'refs/heads/{self.secrets.base_branch}-gh-pages', 'sha': sha}
        r = github_api(
            'post', f'repos/{self.secrets.test_repo}/git/refs', self.secrets.bot_token, json=data)

    def setup_temp_dir(self):
        self.temp_dir = TemporaryDirectory(prefix='tci-')
        with SetDirectory(Path(self.temp_dir.name)):
            # Make PR's from a temporary directory
            logging.info(f'Worktree directory: {self.temp_dir.name}')
            self.repo.git.worktree('add', '--detach', self.temp_dir.name, f'HEAD')
            self.temp_repo = git.Repo(self.temp_dir.name)

            set_git_username_email(self.temp_repo, self.secrets.bot_name, GITHUB_ACTIONS_BOT_EMAIL)
            self.temp_repo.git.checkout('-b', self.secrets.base_branch)
            pathlib.Path(
                f'{self.chart_dir}/{self.secrets.chart_version}').mkdir(parents=True, exist_ok=True)

            # Remove chart files from base branch
            logging.info(
                f"Remove {self.chart_dir}/{self.secrets.chart_version} from {self.secrets.test_repo}:{self.secrets.base_branch}")
            try:
                self.temp_repo.git.rm('-rf', '--cached', f'{self.chart_dir}/{self.secrets.chart_version}')
                self.temp_repo.git.commit(
                    '-m', f'Remove {self.chart_dir}/{self.secrets.chart_version}')
                self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                                f'HEAD:refs/heads/{self.secrets.base_branch}')
            except git.exc.GitCommandError:
                logging.info(
                    f"{self.chart_dir}/{self.secrets.chart_version} not exist on {self.secrets.test_repo}:{self.secrets.base_branch}")

            # Remove the OWNERS file from base branch
            logging.info(
                f"Remove {self.chart_dir}/OWNERS from {self.secrets.test_repo}:{self.secrets.base_branch}")
            try:
                self.temp_repo.git.rm('-rf', '--cached', f'{self.chart_dir}/OWNERS')
                self.temp_repo.git.commit(
                    '-m', f'Remove {self.chart_dir}/OWNERS')
                self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                                f'HEAD:refs/heads/{self.secrets.base_branch}')
            except git.exc.GitCommandError:
                logging.info(
                    f"{self.chart_dir}/OWNERS not exist on {self.secrets.test_repo}:{self.secrets.base_branch}")


    def process_owners_file(self):
        with SetDirectory(Path(self.temp_dir.name)):
            # Create the OWNERS file from the string template
            values = {'bot_name': self.secrets.bot_name,
                    'vendor': self.secrets.vendor, 'chart_name': self.secrets.chart_name}
            content = Template(self.secrets.owners_file_content).substitute(values)
            with open(f'{self.chart_dir}/OWNERS', 'w') as fd:
                fd.write(content)

            # Push OWNERS file to the test_repo
            logging.info(
                f"Push OWNERS file to '{self.secrets.test_repo}:{self.secrets.base_branch}'")
            self.temp_repo.git.add(f'{self.chart_dir}/OWNERS')
            self.temp_repo.git.commit(
                '-m', f"Add {self.secrets.vendor} {self.secrets.chart_name} OWNERS file")
            self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                        f'HEAD:refs/heads/{self.secrets.base_branch}', '-f')

    def process_chart(self, is_tarball: bool):
        with SetDirectory(Path(self.temp_dir.name)):
            if is_tarball:
                # Copy the chart tar into temporary directory for PR submission
                chart_tar = self.secrets.test_chart.split('/')[-1]
                shutil.copyfile(f'{self.old_cwd}/{self.secrets.test_chart}',
                                f'{self.chart_dir}/{self.secrets.chart_version}/{chart_tar}')
            else:
                # Unzip files into temporary directory for PR submission
                extract_chart_tgz(self.secrets.test_chart, f'{self.chart_dir}/{self.secrets.chart_version}', self.secrets, logging)

    def process_report(self):
        with SetDirectory(Path(self.temp_dir.name)):
            # Copy report to temporary location and push to test_repo:pr_branch
            logging.info(
                f"Push report to '{self.secrets.test_repo}:{self.secrets.pr_branch}'")
            tmpl = open(self.secrets.test_report).read()
            values = {'repository': self.secrets.test_repo,
                    'branch': self.secrets.base_branch}
            content = Template(tmpl).substitute(values)
            with open(f'{self.chart_dir}/{self.secrets.chart_version}/report.yaml', 'w') as fd:
                fd.write(content)

    def push_chart(self):
        # Push chart src files to test_repo:pr_branch
        self.temp_repo.git.add(f'{self.chart_dir}/{self.secrets.chart_version}/src')
        if self.test_report:
            self.temp_repo.git.add(f'{self.chart_dir}/{self.secrets.chart_version}/report.yaml')
        self.temp_repo.git.commit(
            '-m', f"Add {self.secrets.vendor} {self.secrets.chart_name} {self.secrets.chart_version} chart source files{' and report' if self.test_report else ''}")

        self.temp_repo.git.push(f'https://x-access-token:{self.secrets.bot_token}@github.com/{self.secrets.test_repo}',
                      f'HEAD:refs/heads/{self.secrets.pr_branch}', '-f')

    def send_pull_request(self):
        data = {'head': self.secrets.pr_branch, 'base': self.secrets.base_branch,
                'title': self.secrets.pr_branch, 'body': os.environ.get('PR_BODY')}

        logging.info(
            f"Create PR with chart source files from '{self.secrets.test_repo}:{self.secrets.pr_branch}'")
        r = github_api(
            'post', f'repos/{self.secrets.test_repo}/pulls', self.secrets.bot_token, json=data)
        j = json.loads(r.text)
        self.secrets.pr_number = j['number']

    def check_workflow_conclusion(self):
        # Check workflow conclusion
        run_id = get_run_id(self.secrets)
        conclusion = get_run_result(self.secrets, run_id)
        if conclusion == 'success':
            logging.info("Workflow run was 'success'")
        else:
            pytest.fail(
                f"Workflow for the submitted PR did not success, run id: {run_id}")

    def check_pull_request_result(self):
        # Check if PR merged
        r = github_api(
            'get', f'repos/{self.secrets.test_repo}/pulls/{self.secrets.pr_number}/merge', self.secrets.bot_token)
        if r.status_code == 204:
            logging.info("PR merged sucessfully")
        else:
            pytest.fail("Workflow for submitted PR success but PR not merged")

    def check_index_yaml(self):
        old_branch = self.repo.active_branch.name
        self.repo.git.fetch(f'https://github.com/{self.secrets.test_repo}.git',
                    '{0}:{0}'.format(f'{self.secrets.base_branch}-gh-pages'), '-f')
        self.repo.git.checkout(f'{self.secrets.base_branch}-gh-pages')
        with open('index.yaml', 'r') as fd:
            try:
                index = yaml.safe_load(fd)
            except yaml.YAMLError as err:
                pytest.fail(f"error parsing index.yaml: {err}")

        entry = self.secrets.vendor + '-' + self.secrets.chart_name
        if entry not in index['entries']:
            pytest.fail(
                f"{self.secrets.chart_name} {self.secrets.chart_version} not added to index")

        version_list = [release['version'] for release in index['entries'][entry]]
        if self.secrets.chart_version not in version_list:
            pytest.fail(
                f"{self.secrets.chart_name} {self.secrets.chart_version} not added to index")

        logging.info("Index updated correctly, cleaning up local branch")
        self.repo.git.checkout(old_branch)
        self.repo.git.branch('-D', f'{self.secrets.base_branch}-gh-pages')

    def check_release_result(self):
        expected_tag = f'{self.secrets.vendor}-{self.secrets.chart_name}-{self.secrets.chart_version}'
        try:
            release = get_release_by_tag(self.secrets, expected_tag)
            logging.info(f"Released '{expected_tag}' successfully")

            chart_tgz = self.secrets.test_chart.split('/')[-1]
            expected_chart_asset = f'{self.secrets.vendor}-{chart_tgz}'
            required_assets = [expected_chart_asset]
            logging.info(f"Check '{required_assets}' is in release assets")
            release_id = release['id']
            get_release_assets(self.secrets, release_id, required_assets)
            return
        finally:
            logging.info(f"Delete release '{expected_tag}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/releases/{release_id}', self.secrets.bot_token)

            logging.info(f"Delete release tag '{expected_tag}'")
            github_api(
                'delete', f'repos/{self.secrets.test_repo}/git/refs/tags/{expected_tag}', self.secrets.bot_token)