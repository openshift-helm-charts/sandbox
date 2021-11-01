Feature: Chart source submission with report
    Partners or redhat associates can publish their chart by submitting
    error-free chart in source format with a report.

    Examples:
    | vendor_type  | vendor    | chart_path                     | report_path               |
    | partners     | hashicorp | tests/data/vault-0.13.0.tgz    | tests/data/report.yaml    |
    | redhat       | redhat    | tests/data/vault-0.13.0.tgz    | tests/data/report.yaml    |

    Scenario Outline: A partner or redhat associate submits an error-free chart source with report
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And an error-free chart source is used in <chart_path> and report in <report_path>
        When the user sends a pull request with the chart and report
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball
