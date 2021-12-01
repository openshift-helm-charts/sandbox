# -*- coding: utf-8 -*-
"""
PR includes a non chart related file
Partners, redhat or community user submit charts which includes a file which is not part of the chart
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
    test_name = 'Test PR Includes A Non Related File'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/pr_includes_a_file_which_is_not_chart_related.feature', "A user submits a chart with non chart related file")
def test_user_submits_chart_with_non_related_file():
    """A user submits a chart with non chart related file"""

@given(parsers.parse("the vendor <vendor> has a valid identity as <vendor_type>"))
def user_has_valid_identity(workflow_test, vendor, vendor_type):
    """the vendor <vendor> has a valid identity as <vendor_type>."""
    workflow_test.set_vendor(vendor, vendor_type)


@given(parsers.parse("an error-free chart source is used in <chart_path>"))
def user_has_created_error_free_chart_src(workflow_test, chart_path):
    """an error-free chart source is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    

@given("user adds a non chart related file")
def user_adds_a_non_chart_related_file(workflow_test):
    """user adds a non chart related file"""
    workflow_test.add_non_chart_related_file()

@when("the user sends a pull request with both chart and non related file")
def user_sends_pull_request_with_chart_and_non_related_file(workflow_test):
    """the user sends a pull request with both chart and non related file"""
    workflow_test.push_chart(is_tarball=False, add_non_chart_file=True)
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
