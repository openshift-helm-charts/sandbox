import argparse
import json
import sys

from submission import serializer, Submission, SubmissionError
from tools import gitutils


def write_submission_to_file(s: Submission, artifact_path: str):
    data = serializer.SubmissionEncoder().encode(s)

    with open(artifact_path, "w") as f:
        f.write(data)


def read_submission_from_file(articact_path: str):
    with open(articact_path, "r") as f:
        s = json.load(f, cls=serializer.SubmissionDecoder)

    return s


def craft_pr_content_error_msg(s: Submission):
    # Checks that this PR is a valid "Chart certification" PR
    is_valid, msg = s.is_valid_certification_submission(ignore_owners=True)
    if not is_valid:
        return False, msg

    # Parse the modified files and determine if it is a "web_catalog_only" certification
    try:
        s.parse_web_catalog_only()
    except SubmissionError as e:
        return False, str(e)

    if s.is_web_catalog_only:
        if not s.is_valid_web_catalog_only():
            msg = "nope"
            return False, msg

    return True, ""


def craft_owners_error_msg(s):
    is_valid, msg = s.is_valid_owners_submission()
    if is_valid:
        msg = "[ERROR] Send OWNERS file by itself in a separate PR."
    return msg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        required=True,
        help="Path to artifact file to write Submission json representation",
    )
    parser.add_argument(
        "-c",
        "--chart_submission",
        dest="check_chart_submission",
        default=False,
        action="store_true",
        help="Signify that the PR referenced by api_url is expected to be a certification submission",
    )

    args = parser.parse_args()
    try:
        s = Submission(args.api_url)
    except SubmissionError as e:
        print(str(e))
        gitutils.add_output("pr-content-error-message", str(e))
        sys.exit(10)

    ### TODO: add check index

    gitutils.add_output("chart_entry_name", s.chart.name)
    gitutils.add_output("release_tag", s.chart.get_release_tag())
    gitutils.add_output("web_catalog_only", s.is_web_catalog_only)
    gitutils.add_output("category", s.chart.category)

    owners_error_msg = ""
    if s.modified_owners:
        # If the PR contains an OWNER file, craft a error message to be added as a comment in the PR
        owners_error_msg = craft_owners_error_msg(s)
        gitutils.add_output("owners-error-message", owners_error_msg)

    pr_content_error_msg = ""
    if args.check_chart_submission:
        pr_content_error_msg = craft_pr_content_error_msg(s)
        if not pr_content_error_msg:
            print(pr_content_error_msg)
            gitutils.add_output("pr-content-error-message", pr_content_error_msg)

    if owners_error_msg or pr_content_error_msg:
        sys.exit(20)

    write_submission_to_file(s, args.output)


if __name__ == "__main__":
    main()
