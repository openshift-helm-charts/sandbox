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


@scenario('../features/HC-16_report_sha.feature', "[HC-19-001] A partner or redhat associate submits an error-free report with report sha value")
def test_report_with_valid_report_sha():
    """A user submits a report with valid report sha value."""

@scenario('../features/HC-16_report_sha.feature', "[HC-19-002] A partner or redhat associate submits a report with invalid report sha value")
def test_report_with_invalid_report_sha():
    """A user submits a report with invalid report sha value."""

