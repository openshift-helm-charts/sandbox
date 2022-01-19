import pytest
from pytest_bdd import scenario, given, parsers


from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Smoke Test'
    test_chart = 'tests/data/vault-0.17.0.tgz'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_chart=test_chart)
    yield workflow_test
    workflow_test.cleanup()

@scenario('../features/smoke/chart_src_without_report.feature', "A partner or redhat associate submits an error-free chart source")
def test_partner_or_redhat_user_submits_chart_src():
    """A partner or redhat associate submits an error-free chart source."""

@scenario('../features/smoke/chart_tar_without_report.feature', "A partner or redhat associate submits an error-free chart tarball")
def test_partner_or_redhat_user_submits_chart_tarball():
    """A partner or redhat associate submits an error-free chart tarball."""

@scenario('../features/smoke/report_and_chart_src.feature', "A partner or redhat associate submits an error-free chart source with report")
def test_partner_or_redhat_user_submits_chart_src_with_report():
    """A partner or redhat associate submits an error-free chart source with report."""

@scenario('../features/smoke/report_and_chart_src.feature', "A community user submits an error-free chart source with report")
def test_community_user_submits_chart_src_with_report():
    """A community user submits an error-free chart source with report"""

@scenario('../features/smoke/report_and_chart_tar.feature', "A partner or redhat associate submits an error-free chart tarball with report")
def test_partners_or_redhat_user_submits_chart_tarball_with_report():
    """A partner or redhat associate submits an error-free chart tarball with report."""

@scenario('../features/smoke/report_and_chart_tar.feature', "A community user submits an error-free chart tarball with report")
def test_community_user_submits_chart_tarball_with_report():
    """A community user submits an error-free chart tarball with report"""

@scenario('../features/smoke/report_without_chart.feature', "A partner or redhat associate submits an error-free report")
def test_partner_or_redhat_user_submits_report():
    """A partner or redhat associate submits an error-free report."""

@scenario('../features/smoke/report_without_chart.feature', "A community user submits an error-free report")
def test_community_user_submits_report():
    """A community user submits an error-free report"""

@scenario('../features/smoke/chart_verifier_comes_back_with_failures.feature', "A partner or community user submits a chart which does not contain a readme file")
def test_partner_or_community_user_submits_chart_without_readme():
    """A partner or community user submits a chart which does not contain a readme file"""

@scenario('../features/smoke/invalid_url_in_the_report.feature', "A user submits a report with an invalid url")
def test_report_submission_with_invalid_url():
    """A user submits a report with an invalid url."""

@scenario('../features/smoke/pr_includes_a_file_which_is_not_chart_related.feature', "A user submits a chart with non chart related file")
def test_user_submits_chart_with_non_related_file():
    """A user submits a chart with non chart related file"""

@scenario('../features/smoke/report_in_json_format.feature', "An user submits an report in json format")
def an_user_submits_report_in_json_format():
    """An user submits an report in json format."""

@scenario('../features/smoke/report_only_edited.feature', "A partner or redhat associate submits an edited report")
def test_partner_or_redhat_user_submits_edited_report():
    """A partner or redhat associate submits an edited report."""

@scenario('../features/smoke/report_with_missing_checks.feature', "A user submits a report with missing checks")
def test_report_submission_with_missing_checks():
    """A user submits a report with missing checks."""

@scenario('../features/smoke/sha_value_does_not_match.feature', "A user submits a chart tarball with report")
def test_chart_submission_with_report():
    """A user submits a chart tarball with report."""

@scenario('../features/smoke/user_submits_chart_with_errors.feature', "An unauthorized user submits a chart")
def test_chart_submission_by_unauthorized_user():
    """An unauthorized user submits a chart"""

@scenario('../features/smoke/user_submits_chart_with_errors.feature', "An authorized user submits a chart with incorrect version")
def test_chart_submission_with_incorrect_version():
    """ An authorized user submits a chart with incorrect version """


@given(parsers.parse("the report has a <check> missing"))
def report_has_a_check_missing(workflow_test, check):
    workflow_test.process_report(missing_check=check)

@given(parsers.parse("the report includes <tested> and <supported> OpenshiftVersion values and chart <kubeversion> value"))
def report_includes_specified_versions(workflow_test,tested,supported,kubeversion):
    workflow_test.process_report(update_versions=True,supported_versions=supported,tested_version=tested,kube_version=kubeversion)


