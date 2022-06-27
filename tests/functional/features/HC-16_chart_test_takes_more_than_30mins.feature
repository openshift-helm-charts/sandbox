Feature: Chart test takes longer time and exceeds default timeout
  Partners, redhat or community user submit charts which result in errors

  Examples:
    | chart_path                                  | message                                                 |
    | tests/data/vault-test-timeout-0.17.0.tgz    | Chart test failure: timed out waiting for the condition |

  Scenario Outline: [HC-16-001] A submitted chart takes more than 30 mins
    Given the vendor <vendor> has a valid identity as <vendor_type>
    And an error-free chart tarball is used in <chart_path>
    When the user sends a pull request with the chart
    Then the pull request is not merged
    And user gets the <message> in the pull request comment

    Examples:
      | vendor_type  | vendor         |
      | partners     | hashicorp      |
      | redhat       | redhat         |
      | community    | redhat         |