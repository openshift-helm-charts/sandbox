# -*- coding: utf-8 -*-
"""
Report contains an invalid URL
Partners, redhat and community users submits only report with an invalid URL
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
    test_name = 'Invalid Chart URL'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/invalid_url_in_the_report.feature', "A user submits a report with an invalid url")
def test_report_submission_with_invalid_url():
    """A user submits a report with an invalid url."""


@given(parsers.parse("the vendor <vendor> has a valid identity as <vendor_type>"))
def user_has_valid_identity(workflow_test, vendor, vendor_type):
    """the vendor <vendor> has a valid identity as <vendor_type>."""
    workflow_test.set_vendor(vendor, vendor_type)


@given(parsers.parse("report used in <report_path>"))
def user_generated_a_report(workflow_test, report_path):
    """report used in <report_path>"""
    workflow_test.update_test_report(report_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()

@given(parsers.parse("the report contains an <invalid_url>"))
def sha_value_does_not_match(workflow_test, invalid_url):
    workflow_test.process_report(update_url=True, url=invalid_url)

@when("the user sends a pull request with the report")
def user_sends_pull_request_with_report(workflow_test):
    """the user sends a pull request with the report"""
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
