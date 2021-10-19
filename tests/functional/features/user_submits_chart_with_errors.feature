Feature: Chart submission with errors
  Partners or redhat associates submit charts which result in errors

  Examples:
  | vendor_type  | vendor    | chart   | version  |
  | partners     | hashicorp | vault   | 0.13.0   |
  | redhat       | redhat    | vault   | 0.13.0   |

  Scenario Outline: An unauthorized user submits a chart with report
    Given A <user> wants to submit a chart
    And <vendor> of <vendor_type> wants to submit <chart> of <version>
    And the user creates a branch to add a new chart version
    When the user sends a pull request with chart and report
    Then the pull request is not merged
    And user gets the <message> with steps to follow for resolving the issue in the pull request

    Examples:
      | message                                          | user         |
      | is not allowed to submit the chart on behalf of  | unauthorized |

  Scenario Outline: An authorized user submits a chart with incorrect version
    Given A <user> wants to submit a chart
    And <vendor> of <vendor_type> wants to submit <chart> of <version>
    And Chart.yaml specifies a <badVersion>
    And the user creates a branch to add a new chart version
    When the user sends a pull request with chart and report
    Then the pull request is not merged
    And user gets the <message> with steps to follow for resolving the issue in the pull request

    Examples:
      | message                               | badVersion | user                      |
      | doesn't match the directory structure | 9.9.9      | openshift-helm-charts-bot |
