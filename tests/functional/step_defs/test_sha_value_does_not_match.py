# -*- coding: utf-8 -*-
"""SHA value in the report does not match
Partners, redhat and community users submits chart tar with report
where tar sha does not match with sha value digests.chart in the report
"""
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
    parsers
)

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'SHA Value Does Not Match'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/sha_value_does_not_match.feature', "A user submits a chart tarball with report")
def test_chart_submission_with_report():
    """A user submits a chart tarball with report."""


@given(parsers.parse("the vendor <vendor> has a valid identity as <vendor_type>"))
def user_has_valid_identity(workflow_test, vendor, vendor_type):
    """the vendor <vendor> has a valid identity as <vendor_type>."""
    workflow_test.set_vendor(vendor, vendor_type)


@given(parsers.parse("a chart tarball is used in <chart_path> and report in <report_path>"))
def user_has_created_a_chart_tarball_and_report(workflow_test, chart_path, report_path):
    """an error-free chart tarball is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    

@given(parsers.parse("the report contains an <error>"))
def sha_value_does_not_match(workflow_test, error):
    if error == 'sha_mismatch':
        workflow_test.process_report(update_chart_sha=True)
    else:
        pytest.fail(f"This {error} handling is not implemented yet")

@when("the user sends a pull request with the chart and report")
def user_sends_pull_request_with_chart_tarball_and_report(workflow_test):
    """the user sends a pull request with the chart and report."""
    workflow_test.push_chart(is_tarball=True)
    workflow_test.send_pull_request()

@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(workflow_test):
    """the pull request is not merged"""
    workflow_test.check_workflow_conclusion(expect_result='failure')
    workflow_test.check_pull_request_result(expect_merged=False)

@then(parsers.parse("user gets the <message> in the pull request comment"))
def user_gets_the_message_in_the_pull_request_comment(workflow_test, message):
    """user gets the message in the pull request comment"""
    workflow_test.check_pull_request_comments(expect_message=message)
