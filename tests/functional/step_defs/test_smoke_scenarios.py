import pytest
from pytest_bdd import scenario, given, parsers, then


from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Smoke Test'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/smoke/user_submits_chart_with_errors.feature', "An authorized user submits a chart with incorrect version")
def test_chart_submission_with_incorrect_version():
    """ An authorized user submits a chart with incorrect version """

@scenario('../features/smoke/provider_delivery_control.feature', "A partner associate submits an error-free report with provider controlled delivery")
def test_partners_submits_error_free_report_for_provider_controlled_delivery():
    """A partner submits an error-free report for provider controlled delivery."""

@given(parsers.parse("the report has a <check> missing"))
def report_has_a_check_missing(workflow_test, check):
    workflow_test.process_report(missing_check=check)

@given(parsers.parse("the report includes <tested> and <supported> OpenshiftVersion values and chart <kubeversion> value"))
def report_includes_specified_versions(workflow_test,tested,supported,kubeversion):
    workflow_test.process_report(update_versions=True,supported_versions=supported,tested_version=tested,kube_version=kubeversion)

@given(parsers.parse("provider delivery control is set to <provider_control_owners> in the OWNERS file"))
def provider_delivery_control_set_in_owners(workflow_test,provider_control_owners):
    if provider_control_owners == "true":
        print("[INFO] set provider delivery control_in owners file")
        workflow_test.check_owners_file_values()
        workflow_test.secrets.provider_delivery=True
    else:
        print("[INFO] un-set provider delivery control_in owners file")
        workflow_test.secrets.provider_delivery=False

@given(parsers.parse("provider delivery control is set to <provider_control_report> in the report"))
def provider_delivery_control_set_in_report(workflow_test,provider_control_report):
    if provider_control_report == "true":
        print("[INFO] set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=True)
    else:
        print("[INFO] un-set provider delivery control_in report")
        workflow_test.process_report(update_provider_delivery=True,provider_delivery=False)

@then(parsers.parse("the <index_file> is updated with an entry for the submitted chart"))
def index_file_is_updated(workflow_test,index_file):
    workflow_test.secrets.index_file = index_file


