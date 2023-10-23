import os
import sys
from tools import gitutils


def get_success_coment():
    return (
        "Congratulations! Your chart has been certified and will be published shortly."
    )


def get_content_failure_message():
    return "One or more errors were found with the pull request:"


def get_community_review_message():
    return "Community charts require maintainer review and approval, a review will be conducted shortly."


def get_failure_comment():
    return (
        "There were one or more errors while building and verifying your pull request."
    )


def get_verifier_errors_comment():
    return "[ERROR] The submitted chart has failed certification. Reason(s):"


def get_verifier_errors_trailer():
    return "Please create a valid report with the [chart-verifier](https://github.com/redhat-certification/chart-verifier) \
and ensure all mandatory checks pass."


def get_look_at_job_output_comment():
    return """To see the console output with the error messages, click the "Details" \
link next to "CI / Chart Certification" job status towards the end of this page."""


def prepare_failure_comment():
    """assembles the comment for certification failures

    Will attempt to read a file with error messaging from the filesystem
    and included that information in its content. (e.g. ./pr/errors)
    """
    msg = get_failure_comment()
    msg = append_to(msg, get_look_at_job_output_comment())
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg = append_to(msg, get_verifier_errors_comment())
        msg = append_to(msg, errors)
        msg = append_to(msg, get_verifier_errors_trailer())
        gitutils.add_output("error-message", errors)
    else:
        gitutils.add_output("error-message", get_failure_comment())
    return msg


def prepare_pr_content_failure_comment():
    msg = f"{get_content_failure_message()}"
    pr_content_error_msg = os.environ.get("PR_CONTENT_ERROR_MESSAGE", "")
    owners_error_msg = os.environ.get("OWNERS_ERROR_MESSAGE", "")
    if pr_content_error_msg:
        gitutils.add_output("error-message", pr_content_error_msg)
        msg += f"{pr_content_error_msg}"
    if owners_error_msg:
        gitutils.add_output("error-message", owners_error_msg)
        msg += f"{owners_error_msg}"
    return msg


def prepare_run_verifier_failure_comment():
    verifier_error_msg = os.environ.get("VERIFIER_ERROR_MESSAGE", "")
    gitutils.add_output("error-message", verifier_error_msg)
    msg = verifier_error_msg
    msg = append_to(msg, get_look_at_job_output_comment())
    return msg


def prepare_community_comment():
    msg = f"{get_community_review_message()}"
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += "However, please note that one or more errors were found while building and verifying your pull request:"
        msg += f"{errors}"
    return msg


def prepare_generic_fail_comment():
    msg = ""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += "One or more errors were found while building and verifying your pull request:"
        msg += f"{errors}"
    else:
        msg += "An unspecified error has occured while building and verifying your pull request."
    return msg


def prepare_oc_install_fail_comment():
    msg = "Unfortunately the certification process failed to install OpenShift Client and could not complete.\n\n"
    msg += "This problem will be addressed by maintainers and no further action is required from the submitter at this time.\n\n"
    return msg


def append_to(msg, new_content, use_horizontal_divider=False):
    """Appends new_content to the msg.

    This utility function helps simplify the building of our PR comment
    template.

    Developer Note: The use of rstrip and lstrip methods is a developer
    optimization. It's intended to allow us to use a multi-line string but work
    entirely at the same indentation level in source code.

    Args:
        msg: The original message to which we should append new_content.
        new_content: the new string to add.
        use_horizontal_divider: Whether to divide the content
          with a horizontal line (in markdown.) Horizontal lines are
          surrounded in newlines to ensure that it doesn not inadvertently
          cause preceding content to become a Header.

    Returns the msg containing the new content.
    """
    divider_string = ""
    if use_horizontal_divider:
        divider_string = "\n---\n"

    return f"""
{msg}
{divider_string}
{new_content}
""".rstrip().lstrip()


def get_support_information():
    reqs_doc_link = "https://github.com/redhat-certification/chart-verifier/blob/main/docs/helm-chart-checks.md#types-of-helm-chart-checks"
    support_link = "https://redhat-connect.gitbook.io/red-hat-partner-connect-general-guide/managing-your-account/getting-help/technology-partner-success-desk"
    return f"""For information on the certification process see:
- [Red Hat certification requirements and process for Kubernetes applications that are deployed using Helm charts.]({reqs_doc_link}).
For support, connect with our [Technology Partner Acceleration Desk]({support_link})."""


def metadata_label(vendor_label, chart_name):
    """Returns the metadata context that must suffix PR comments."""
    return (
        f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}'
    )


def task_table(task_tuples):
    """returns a markdown table containing tasks and their outcome

    Args:
        task_tuples: a list of two-length tuples where index 0 is the task
          and index 1 is the outcome. These values should be short.
    """
    sorted(task_tuples)
    msg = "|task|outcome|"
    msg += "\n|---|---|"
    for task_tuple in task_tuples:
        msg += f"\n|{task_tuple[0]}|{task_tuple[1]}|"
    return msg


def overall_outcome(outcome):
    if not outcome:
        outcome = "unknown"
    return f"Outcome: **{outcome}**"


def main():
    pr_content_result = sys.argv[1]
    run_verifier_result = sys.argv[2]
    verify_result = sys.argv[3]
    issue_number = open("./pr/NR").read().strip()
    vendor_label = open("./pr/vendor").read().strip()
    chart_name = open("./pr/chart").read().strip()

    community_manual_review = os.environ.get("COMMUNITY_MANUAL_REVIEW", False)
    oc_install_result = os.environ.get("OC_INSTALL_RESULT", False)

    msg = f"Thank you for submitting PR #{issue_number} for Helm Chart Certification!"

    msg = append_to(msg, "### Detail")
    outcome = "Failed"

    # Handle success explicitly
    if (
        pr_content_result == "success"
        and run_verifier_result == "success"
        and verify_result == "success"
        and oc_install_result == "success"
    ):
        outcome = "Passed"
        msg = append_to(msg, get_success_coment())
        gitutils.add_output("pr_passed", "true")
    else:  # Handle various failure scenarios.
        if pr_content_result == "failure":
            msg = append_to(msg, prepare_pr_content_failure_comment())
            gitutils.add_output("pr_passed", "false")
        elif run_verifier_result == "failure":
            msg = append_to(msg, prepare_run_verifier_failure_comment())
            gitutils.add_output("pr_passed", "false")
        elif verify_result == "failure":
            if community_manual_review:
                outcome = "Pending Manual Review"
                msg = append_to(msg, prepare_community_comment())
                gitutils.add_output("pr_passed", "true")
            else:
                msg = append_to(msg, prepare_failure_comment())
                gitutils.add_output("pr_passed", "false")
        elif oc_install_result == "failure":
            msg = append_to(msg, prepare_oc_install_fail_comment())
            gitutils.add_output("pr_passed", "false")
        else:
            msg = append_to(msg, prepare_generic_fail_comment())
            gitutils.add_output("pr_passed", "false")

    if outcome != "Passed":
        table = task_table(
            [
                ("PR Content Check", pr_content_result),
                ("Run Chart Verifier", run_verifier_result),
                ("Result Verification", verify_result),
                ("OpenShift Client Installation", oc_install_result),
            ]
        )
        msg = append_to(msg, "### Task Insights")
        msg = append_to(msg, "Here are the outcomes of tasks driving this result.")
        msg = append_to(msg, table)

    # All comments get helpful links and a metadata
    msg = append_to(msg, overall_outcome(outcome), use_horizontal_divider=True)
    msg = append_to(msg, get_support_information(), use_horizontal_divider=True)
    msg = append_to(msg, metadata_label(vendor_label, chart_name))

    # Print to the console so it's easily visible from CI.
    print("*" * 30)
    print(msg)
    print("*" * 30)

    with open("./pr/comment", "w") as fd:
        fd.write(msg)
        gitutils.add_output("message-file", fd.name)


if __name__ == "__main__":
    main()
