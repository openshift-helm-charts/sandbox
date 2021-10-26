# -*- coding: utf-8 -*-
"""Chart source only submission

Partners or redhat associates can publish their chart by submitting
error-free chart in source format without the report.
"""
import os
import json
import base64
import pathlib
import tarfile
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

from functional.utils.utils import *
from functional.utils.certification_workflow_test import CertificationWorkflowTestOneShot
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def secrets():
    test_chart = 'tests/data/vault-0.13.0.tgz'
    workflow_test = CertificationWorkflowTestOneShot(test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/chart_src_without_report.feature', "The partner hashicorp submits a error-free chart source for vault")
def test_partner_chart_src_submission():
    """The partner hashicorp submits a error-free chart source for vault."""


@scenario('../features/chart_src_without_report.feature', "A redhat associate submits a error-free chart source for vault")
def test_redhat_chart_src_submission():
    """A redhat associate submits a error-free chart source for vault."""


@given("hashicorp is a valid partner")
def hashicorp_is_a_valid_partner(secrets):
    """hashicorp is a valid partner"""
    secrets.set_vendor(get_unique_vendor('hashicorp'), 'partners')


@given("a redhat associate has a valid identity")
def redhat_associate_is_valid(secrets):
    """a redhat associate has a valid identity"""
    secrets.set_vendor(get_unique_vendor('redhat'), 'redhat')


@given("hashicorp has created an error-free chart source for vault")
@given("the redhat associate has created an error-free chart source for vault")
def the_user_has_created_a_error_free_chart_src(secrets):
    """The user has created an error-free chart source."""

    secrets.setup_git_context()
    secrets.setup_gh_pages_branch()
    secrets.setup_temp_dir()
    secrets.process_owners_file()
    secrets.process_chart(is_tarball=False)
    secrets.push_chart()


@when("hashicorp sends a pull request with the vault source chart")
@when("the redhat associate sends a pull request with the vault source chart")
def the_user_sends_the_pull_request_with_the_chart_src(secrets):
    """The user sends the pull request with the chart source files."""
    secrets.send_pull_request()


@then("hashicorp sees the pull request is merged")
@then("the redhat associate sees the pull request is merged")
def the_user_should_see_the_pull_request_getting_merged(secrets):
    """The user should see the pull request getting merged."""
    secrets.check_workflow_conclusion()
    secrets.check_pull_request_result()


@then("the index.yaml file is updated with an entry for the submitted chart")
def the_index_yaml_is_updated_with_a_new_entry(secrets):
    """The index.yaml file is updated with a new entry."""
    secrets.check_index_yaml()


@then("a release for the vault chart is published with corresponding report and chart tarball")
def the_release_is_published(secrets):
    """a release is published with the chart"""
    secrets.check_release_result()
