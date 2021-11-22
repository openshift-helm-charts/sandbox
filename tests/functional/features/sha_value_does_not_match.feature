Feature: SHA value in the report does not match
    Partners, redhat and community users submits chart tar with report
    where chart sha does not match with sha value digests.chart in the report

    Examples:
      | chart_path                     | report_path               | message                 |
      | tests/data/vault-0.13.0.tgz    | tests/data/report.yaml    | Digest is not matching  | 
    
    Scenario Outline: A user submits a chart tarball with report
        Given the vendor <vendor> has a valid identity as <vendor_type>
        And a chart tarball is used in <chart_path> and report in <report_path>
        And the sha value of chart in report does not match the chart sha value
        When the user sends a pull request with the chart and report
        Then the pull request is not merged
        And user gets the <message> in the pull request comment

        Examples:
            | vendor_type  | vendor    |
            | partners     | hashicorp |
            | redhat       | redhat    |
            | community    | redhat    |
