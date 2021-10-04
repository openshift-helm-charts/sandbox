Feature: Chart submitted by an unauthorized user
    Partners or redhat associates can not submit charts if they are not in the OWNERS file of the chart

    Scenario: An unauthorized user submits a chart with report 
        Given user is not present in the OWNERS file of the chart
	And the user creates a branch to add a new chart version
        When the user sends a pull request with chart and report
        Then the pull request is not merged
        And user gets the message with steps to follow for resolving the issue in the pull request
