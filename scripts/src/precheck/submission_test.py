import pytest
import responses
import sys

sys.path.append(".")
from submission import Submission, DuplicateChartError, SubmissionError, VersionError

expected_category = "partners"
expected_organization = "acme"
expected_chart = "awesome"
expected_version = "1.42.0"


@responses.activate
def test_submission_report():
    """Test case when a user provides a valid report"""
    submission_with_report = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/1"
    )
    expected_report_path = f"charts/{expected_category}/{expected_organization}/{expected_chart}/{expected_version}/report.yaml"

    responses.get(
        f"{submission_with_report}/files", json=[{"filename": expected_report_path}]
    )

    s = Submission(api_url=submission_with_report)

    assert s.api_url == submission_with_report
    assert expected_report_path in s.modified_files
    assert s.report.found
    assert not s.report.signed
    assert s.report.path == expected_report_path


@responses.activate
def test_submission_source():
    """Test case when a user provides the source of the chart to certify"""
    submission_with_source = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/2"
    )
    expected_report_source_basepath = f"charts/{expected_category}/{expected_organization}/{expected_chart}/{expected_version}/src"

    responses.get(
        f"{submission_with_source}/files",
        json=[
            {"filename": f"{expected_report_source_basepath}/Chart.yaml"},
            {
                "filename": f"{expected_report_source_basepath}/templates/buildconfig.yaml"
            },
            {
                "filename": f"{expected_report_source_basepath}/templates/deployment.yaml"
            },
            {
                "filename": f"{expected_report_source_basepath}/templates/imagestream.yaml"
            },
            {"filename": f"{expected_report_source_basepath}/templates/route.yaml"},
            {"filename": f"{expected_report_source_basepath}/templates/service.yaml"},
            {"filename": f"{expected_report_source_basepath}/values.schema.json"},
            {"filename": f"{expected_report_source_basepath}/values.yaml"},
        ],
    )

    s = Submission(api_url=submission_with_source)

    assert s.api_url == submission_with_source

    assert f"{expected_report_source_basepath}/Chart.yaml" in s.modified_files
    assert (
        f"{expected_report_source_basepath}/templates/buildconfig.yaml"
        in s.modified_files
    )
    assert (
        f"{expected_report_source_basepath}/templates/deployment.yaml"
        in s.modified_files
    )
    assert (
        f"{expected_report_source_basepath}/templates/imagestream.yaml"
        in s.modified_files
    )
    assert f"{expected_report_source_basepath}/templates/route.yaml" in s.modified_files
    assert (
        f"{expected_report_source_basepath}/templates/service.yaml" in s.modified_files
    )
    assert f"{expected_report_source_basepath}/values.schema.json" in s.modified_files
    assert f"{expected_report_source_basepath}/values.yaml" in s.modified_files

    assert s.source.found
    # Source path points to the Chart.yaml
    assert s.source.path == f"{expected_report_source_basepath}/Chart.yaml"


@responses.activate
def test_submission_tarball():
    """Test case when a user provides an unsigned tarball"""
    submission_with_tarball = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/3"
    )
    expected_tarball_path = f"charts/{expected_category}/{expected_organization}/{expected_chart}/{expected_version}/{expected_chart}-{expected_version}.tgz"

    responses.get(
        f"{submission_with_tarball}/files", json=[{"filename": expected_tarball_path}]
    )

    s = Submission(api_url=submission_with_tarball)

    assert s.api_url == submission_with_tarball
    assert expected_tarball_path in s.modified_files
    assert s.tarball.found
    assert not s.tarball.provenance
    assert s.tarball.path == expected_tarball_path


@responses.activate
def test_submission_not_exist():
    """Test creating a Submission for an unexisting PR"""
    api_url_doesnt_exist = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/9999"
    )

    responses.get(
        f"{api_url_doesnt_exist}/files",
        json={
            "message": "Not Found",
            "documentation_url": "https://docs.github.com/rest/pulls/pulls#list-pull-requests-files",
        },
    )

    with pytest.raises(SubmissionError):
        Submission(api_url=api_url_doesnt_exist)


@responses.activate
def test_submission_more_than_one_chart():
    """Test case when a user attempts to add more than one chart"""
    submission_more_than_one_chart = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/4"
    )

    first_report = f"charts/{expected_category}/{expected_organization}/{expected_chart}/{expected_version}/report.yaml"
    second_report = f"charts/{expected_category}/{expected_organization}/other-chart/{expected_version}/report.yaml"

    responses.get(
        f"{submission_more_than_one_chart}/files",
        json=[{"filename": first_report}, {"filename": second_report}],
    )

    with pytest.raises(DuplicateChartError):
        Submission(api_url=submission_more_than_one_chart)


@responses.activate
def test_submission_version_not_semver():
    """Test case when a user attempts to add more than one chart"""
    submission_version_not_semver = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/5"
    )

    expected_report = f"charts/{expected_category}/{expected_organization}/{expected_chart}/0.1.2.3.4.5/report.yaml"

    responses.get(
        f"{submission_version_not_semver}/files", json=[{"filename": expected_report}]
    )

    with pytest.raises(VersionError):
        Submission(api_url=submission_version_not_semver)
