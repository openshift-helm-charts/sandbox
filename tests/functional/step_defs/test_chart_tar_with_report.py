# -*- coding: utf-8 -*-
"""Report and chart tar submission

Partners or redhat associates can publish their chart by submitting
error-free chart in tar format with the report.
"""
import logging

import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from functional.utils.utils import *
from functional.utils.certification_workflow_test import CertificationWorkflowTestOneShot

@pytest.fixture
def workflow_test():
    test_name = 'Test Chart Tarball With Report'
    test_chart = 'tests/data/vault-0.13.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = CertificationWorkflowTestOneShot(name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/report_and_chart_tar.feature', "The partner hashicorp submits an error-free chart tar with report for vault")
def test_partner_chart_tar_with_report_submission():
    """The partner hashicorp submits an error-free chart tar with report for vault."""


@scenario('../features/report_and_chart_tar.feature', "A redhat associate submits an error-free chart tar with report for vault")
def test_redhat_chart_tar_with_report_submission():
    """A redhat associate submits an error-free chart tar with report for vault."""


@given("hashicorp is a valid partner")
def hashicorp_is_a_valid_partner(workflow_test):
    """hashicorp is a valid partner"""
    workflow_test.set_vendor(get_unique_vendor('hashicorp'), 'partners')


@given("a redhat associate has a valid identity")
def redhat_associate_is_valid(workflow_test):
    """a redhat associate has a valid identity"""
    workflow_test.set_vendor(get_unique_vendor('redhat'), 'redhat')


@given("hashicorp has created an error-free chart tar and report for vault")
@given("the redhat associate has created an error-free chart tar and report for vault")
def the_user_has_created_a_error_free_chart_tar_with_report(workflow_test):
    """The user has created an error-free chart tar."""
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    workflow_test.process_report()
    workflow_test.push_chart(is_tarball=True)

@when("hashicorp sends a pull request with the vault tar chart and report")
@when("the redhat associate sends a pull request with the vault tar chart and report")
def the_user_sends_the_pull_request(workflow_test):
    """The user sends the pull request with the chart tar files."""
    workflow_test.send_pull_request()


@then("hashicorp sees the pull request is merged")
@then("the redhat associate sees the pull request is merged")
def the_user_should_see_the_pull_request_getting_merged(workflow_test):
    """The user should see the pull request getting merged."""
    workflow_test.check_workflow_conclusion(expect_result='success')
    workflow_test.check_pull_request_result(expect_merged=True)


@then("the index.yaml file is updated with an entry for the submitted chart")
def the_index_yaml_is_updated_with_a_new_entry(workflow_test):
    """The index.yaml file is updated with a new entry."""
    workflow_test.check_index_yaml()


@then("a release for the vault chart is published with corresponding report and chart tarball")
def the_release_is_published(workflow_test):
    """a release is published with the chart"""
    workflow_test.check_release_result()
