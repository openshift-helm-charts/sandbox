# -*- coding: utf-8 -*-
"""
Report does not include a check
Partners, redhat and community users submits only report which does not include full set of checks
"""
import pytest
from pytest_bdd import (
    scenario,
    given,
    parsers
)

from functional.utils.chart_certification import ChartCertificationE2ETestSingle

@pytest.fixture
def workflow_test():
    test_name = 'Report with report sha value'
    test_report = 'tests/data/report.yaml'
    workflow_test = ChartCertificationE2ETestSingle(test_name=test_name, test_report=test_report)
    yield workflow_test
    workflow_test.cleanup()


@scenario('../features/HC-16_report_sha.feature', "[HC-16-001] A partner or redhat associate submits an error-free report with report sha value")
def test_report_with_valid_report_sha():
    """A user submits a report with valid report sha value."""

@scenario('../features/HC-16_report_sha.feature', "[HC-16-002] A partner or redhat associate submits a report with invalid report sha value")
def test_report_with_invalid_report_sha():
    """A user submits a report with invalid report sha value."""

@scenario('../features/HC-12_report_without_chart.feature', "[HC-12-001] A partner or redhat associate submits an error-free report")
def test_partner_or_redhat_user_submits_report():
    """A partner or redhat associate submits an error-free report."""

@scenario('../features/HC-12_report_without_chart.feature', "[HC-12-002] A community user submits an error-free report")
def test_community_user_submits_report():
    """A community user submits an error-free report"""

