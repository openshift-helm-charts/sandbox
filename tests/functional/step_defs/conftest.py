from pytest_bdd import (
    given,
    then,
    when,
    parsers
)

########### GIVEN ####################
@given(parsers.parse("A <user> wants to submit a chart in <chart_path>"))
def user_wants_to_submit_a_chart(workflow_test, user, chart_path):
    """A <user> wants to submit a chart in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.secrets.bot_name = user

@given(parsers.parse("<vendor> of <vendor_type> wants to submit <chart> of <version>"))
def vendor_of_vendor_type_wants_to_submit_chart_of_version(workflow_test, vendor, vendor_type, chart, version):
    """<vendor> of <vendor_type> wants to submit <chart> of <version>"""
    workflow_test.set_vendor(vendor, vendor_type)
    workflow_test.chart_name, workflow_test.chart_version = chart, version

@given(parsers.parse("Chart.yaml specifies a <bad_version>"))
def chart_yaml_specifies_bad_version(workflow_test, bad_version):
    """ Chart.yaml specifies a <bad_version> """
    if bad_version != '':
        workflow_test.secrets.bad_version = bad_version

@given(parsers.parse("the vendor <vendor> has a valid identity as <vendor_type>"))
def user_has_valid_identity(workflow_test, vendor, vendor_type):
    """the vendor <vendor> has a valid identity as <vendor_type>."""
    workflow_test.set_vendor(vendor, vendor_type)

@given(parsers.parse("an error-free chart source is used in <chart_path> and report in <report_path>"))
def user_has_created_error_free_chart_src_and_report(workflow_test, chart_path, report_path):
    """an error-free chart source is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    workflow_test.process_report()
    workflow_test.push_chart(is_tarball=False)

@given(parsers.parse("an error-free chart source is used in <chart_path>"))
def user_has_created_error_free_chart_src(workflow_test, chart_path):
    """an error-free chart source is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    workflow_test.push_chart(is_tarball=False)

@given(parsers.parse("an error-free chart tarball is used in <chart_path> and report in <report_path>"))
def user_has_created_error_free_chart_tarball_and_report(workflow_test, chart_path, report_path):
    """an error-free chart tarball is used in <chart_path> and report in <report_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.update_test_report(report_path)

    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    workflow_test.process_report()
    workflow_test.push_chart(is_tarball=True)

@given(parsers.parse("an error-free chart tarball is used in <chart_path>"))
def user_has_created_error_free_chart_tarball(workflow_test, chart_path):
    """an error-free chart tarball is used in <chart_path>."""
    workflow_test.update_test_chart(chart_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=True)
    workflow_test.push_chart(is_tarball=True)

@given(parsers.parse("an error-free report is used in <report_path>"))
def user_has_created_error_free_report(workflow_test, report_path):
    """an error-free report is used in <report_path>."""
    workflow_test.update_test_report(report_path)
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_report()

@given("the user creates a branch to add a new chart version")
def the_user_creates_a_branch_to_add_a_new_chart_version(workflow_test):
    """the user creates a branch to add a new chart version."""
    workflow_test.setup_git_context()
    workflow_test.setup_gh_pages_branch()
    workflow_test.setup_temp_dir()
    workflow_test.process_owners_file()
    workflow_test.process_chart(is_tarball=False)
    if workflow_test.secrets.bad_version:
        workflow_test.update_chart_version_in_chart_yaml(workflow_test.secrets.bad_version)
    workflow_test.push_chart(is_tarball=False)
    
############### WHEN ####################
@when("the user sends a pull request with the report")
@when("the user sends a pull request with the chart")
@when("the user sends a pull request with the chart and report")
def user_sends_pull_request_with_chart_src_and_report(workflow_test):
    """the user sends a pull request with the chart and report."""
    workflow_test.send_pull_request()

################ THEN ################
@then("the user sees the pull request is merged")
def user_should_see_pull_request_getting_merged(workflow_test):
    """the user sees the pull request is merged."""
    workflow_test.check_workflow_conclusion(expect_result='success')
    workflow_test.check_pull_request_result(expect_merged=True)

@then("the pull request is not merged")
def the_pull_request_is_not_getting_merged(workflow_test):
    """the pull request is not merged"""
    workflow_test.check_workflow_conclusion(expect_result='failure')
    workflow_test.check_pull_request_result(expect_merged=False)

@then("the index.yaml file is updated with an entry for the submitted chart")
def index_yaml_is_updated_with_new_entry(workflow_test):
    """the index.yaml file is updated with an entry for the submitted chart."""
    workflow_test.check_index_yaml()


@then("a release is published with corresponding report and chart tarball")
def release_is_published(workflow_test):
    """a release is published with corresponding report and chart tarball."""
    workflow_test.check_release_result()

@then(parsers.parse("user gets the <message> in the pull request comment"))
def user_gets_the_message_in_the_pull_request_comment(workflow_test, message):
    """user gets the message in the pull request comment"""
    workflow_test.check_pull_request_comments(expect_message=message)
