Feature: Chart source submission without report
    Partners or redhat associates can publish their chart by submitting
    error-free chart in source format without a report.

    Examples:
    | vendor_type  | vendor    | chart_path                     |
    | partners     | hashicorp | tests/data/vault-0.13.0.tgz    |
    | redhat       | redhat    | tests/data/vault-0.13.0.tgz    |

    Scenario Outline: A partner or redhat associate submits an error-free chart source
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And an error-free chart source is used in <chart_path>
        When the user sends a pull request with the chart
        Then the user sees the pull request is merged
        And the index.yaml file is updated with an entry for the submitted chart
        And a release is published with corresponding report and chart tarball
