import os
import requests
import semver

from dataclasses import dataclass

from checkprcontent import checkpr

xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


class SubmissionError(Exception):
    """Root Exception for handling any error with with the submission"""

    pass


class DuplicateChartError(SubmissionError):
    """This Exception is to be raised when the user attempts to submit a PR with more than one chart"""

    pass


class VersionError(SubmissionError):
    """This Exception is to be raised when the version of the chart is not semver compatible"""

    pass


class OwnersFileError(SubmissionError):
    """This Exception is to be raised when the user incorrectly attempts to submit an OWNER file"""

    pass


@dataclass
class Chart:
    category: str = None
    organization: str = None
    version: str = None
    name: str = None

    def register_chart_info(self, category, organization, name, version):
        if (
            (self.category and self.category != category)
            or (self.organization and self.organization != organization)
            or (self.name and self.name != name)
            or (self.version and self.version != version)
        ):
            msg = "[ERROR] A PR must contain only one chart. Current PR includes files for multiple charts."
            print(msg)
            raise DuplicateChartError(msg)

        if not semver.VersionInfo.isvalid(version):
            msg = (
                f"[ERROR] Helm chart version is not a valid semantic version: {version}"
            )
            print(msg)
            raise VersionError(msg)

        self.category = category
        self.organization = organization
        self.name = name
        self.version = version


@dataclass
class Report:
    found: bool = False
    signed: bool = False
    path: str = None


@dataclass
class Source:
    found: bool = False
    path: str = None  # Path to the Chart.yaml


@dataclass
class Tarball:
    found: bool = False
    path: str = None
    provenance: str = None


class Submission:
    api_url: str
    modified_files: list[str]
    chart: Chart
    report: Report
    source: Source
    tarball: Tarball

    def __init__(self, api_url):
        self.api_url = api_url
        self.modified_files = []
        self.chart = Chart()
        self.report = Report()
        self.source = Source()
        self.tarball = Tarball()

        self._get_modified_files()
        self._parse_modified_files()

    def _get_modified_files(self):
        """Query the GitHub API in order to retrieve the list of files that are added / modified by this PR"""
        page_number = 1
        max_page_size, page_size = 100, 100
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        files_api_url = f"{self.api_url}/files"

        while page_size == max_page_size:
            files_api_query = f"{files_api_url}?per_page={page_size}&page={page_number}"
            print(f"[INFO] Query files : {files_api_query}")
            r = requests.get(files_api_query, headers=headers)
            files = r.json()
            page_size = len(files)
            page_number += 1

            if xRateLimit in r.headers:
                print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
            if xRateRemain in r.headers:
                print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

            if "message" in files:
                msg = f'[ERROR] getting pr files: {files["message"]}'
                print(msg)
                raise SubmissionError(msg)
            else:
                for file in files:
                    if "filename" in file:
                        self.modified_files.append(file["filename"])

    def _parse_modified_files(self):
        """Classify the list of modified files.

        This method will populate the chart, report, source and tarball attributes.

        We expect the user to provide either:
        * Only a report file
        * Only a chart - either as source or tarball (potentially accompagnied by provenance file)
        * Both the report and the chart

        Raises a SubmissionError if:
        * The Submission concerns more than one chart
        * The version of the chart is not SemVer compatible
        * The tarball file is names incorrectly
        * The PR contains additional files, not related to the Chart being submitted
        * The user attempts to create the OWNERS file for its project.

        """
        pattern, reportpattern, tarballpattern = (
            checkpr.get_file_match_compiled_patterns()
        )
        matches_found = 0
        none_chart_files = {}

        for file_path in self.modified_files:
            match = pattern.match(file_path)
            if not match:
                file_name = os.path.basename(file_path)
                none_chart_files[file_name] = file_path
            else:
                self.chart.register_chart_info(*match.groups())

                matches_found += 1
                tar_match = tarballpattern.match(file_path)
                if tar_match:
                    self.tarball.found = True
                    self.tarball.path = file_path
                    print(f"[INFO] tarball found: {file_path}")
                    _, _, chart_name, chart_version, tar_name = tar_match.groups()
                    expected_tar_name = f"{chart_name}-{chart_version}.tgz"
                    if tar_name != expected_tar_name:
                        msg = f"[ERROR] the tgz file is named incorrectly. Expected: {expected_tar_name}. Got: {tar_name}"
                        print(msg)
                        raise SubmissionError(msg)
                elif reportpattern.match(file_path):
                    print(f"[INFO] Report found: {file_path}")
                    self.report.found = True
                    self.report.path = file_path
                elif os.path.basename(file_path) == "Chart.yaml":
                    self.source.found = True
                    self.source.path = file_path

        if none_chart_files:
            if len(self.modified_files) > 1 or "OWNERS" not in none_chart_files:
                # OWNERS not present or preset but not the only file
                msg = (
                    "[ERROR] PR includes one or more files not related to charts: "
                    + ", ".join(none_chart_files)
                )
                print(msg)
                raise SubmissionError(msg)

            if "OWNERS" in none_chart_files:
                file_path = none_chart_files["OWNERS"]
                path_parts = file_path.split("/")
                category = path_parts[1]  # Second after charts
                if category == "partners":
                    msg = "[ERROR] OWNERS file should never be set directly by partners. See certification docs."
                    print(msg)
                    raise OwnersFileError(msg)
                elif matches_found > 0:
                    # There is a mix of chart and non-chart files including OWNERS
                    msg = "[ERROR] Send OWNERS file by itself in a separate PR."
                    print(msg)
                    raise OwnersFileError(msg)
                elif len(self.modified_files) == 1:
                    # OWNERS file is the only file in PR
                    msg = "[INFO] OWNERS file changes require manual review by maintainers."
                    print(msg)
                    raise OwnersFileError(msg)
