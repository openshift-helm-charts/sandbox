from behave import given, when, then

@given(u'the vendor "{vendor}" has a valid identity as "{vendor_type}"')
def vendor_has_valid_identity(context, vendor, vendor_type):
    context.workflow_test.set_vendor(vendor, vendor_type)

@given(u'an error-free chart source is used in "{chart_path}"')
def chart_source_is_used(context, chart_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=False)
    context.workflow_test.push_chart(is_tarball=False)

@given(u'an error-free chart tarball is used in "{chart_path}"')
def user_has_created_error_free_chart_tarball(context, chart_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=True)
    context.workflow_test.push_chart(is_tarball=True)

@when(u'the user sends a pull request with the chart')
def user_sends_a_pull_request(context):
    context.workflow_test.send_pull_request()

@then(u'the user sees the pull request is merged')
def pull_request_is_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='success')
    context.workflow_test.check_pull_request_result(expect_merged=True)

@then(u'the index.yaml file is updated with an entry for the submitted chart')
def index_yaml_updated_with_submitted_chart(context):
    context.workflow_test.check_index_yaml()

@then(u'a release is published with corresponding report and chart tarball')
def release_is_published(context):
    context.workflow_test.check_release_result()

@then(u'the pull request is not merged')
def pull_request_is_not_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='failure')
    context.workflow_test.check_pull_request_result(expect_merged=False)

@then(u'user gets the "{message}" in the pull request comment')
def user_gets_a_message(context, message):
    context.workflow_test.check_pull_request_comments(expect_message=message)


