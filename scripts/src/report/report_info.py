
import os
import sys
import json
import subprocess

REPORT_ANNOTATIONS = "annotations"
REPORT_RESULTS = "results"
REPORT_DIGESTS = "digests"
REPORT_METADATA = "metadata"

def _get_report_info(report_path, info_type, profile_type, profile_version):
    openshift_tools_installer_output = json.loads(os.environ.get("OPENSHIFT_TOOLS_INSTALLER_OUTPUT"))
    if "chart-verifier" not in openshift_tools_installer_output:
        print("[ERROR] report_info: missing OPENSHIFT_TOOLS_INSTALLER_OUTPUT")
        sys.exit(1)
    chart_verifier_binary_path = openshift_tools_installer_output['chart-verifier'].get("installedPath", None)
    if not chart_verifier_binary_path:
        print("[ERROR] report_info: missing 'chart-verifier' binary")
        sys.exit(1)

    command = [chart_verifier_binary_path, "report", info_type, report_path]

    set_values = ""
    if profile_type:
        set_values = "profile.vendortype=%s" % profile_type
    if profile_version:
        if set_values:
            set_values = "%s,profile.version=%s" % (set_values,profile_version)
        else:
            set_values = "profile.version=%s" % profile_version

    if set_values:
        command.extend(["--set", set_values])

    print(f'[INFO] calling chart-verifier: {command}, report path: {report_path}')
    output = subprocess.run(command, capture_output=True)

    # XXX
    print(f'[INFO] [STDOUT] {output.stdout.decode("utf-8")} [STDERR] {output.stderr.decode("utf-8")}')

    report_out = json.loads(output.stdout.decode("utf-8"))

    if not info_type in report_out:
        print(f"Error extracting {info_type} from the report:", report_out.strip())
        sys.exit(1)

    if info_type == REPORT_ANNOTATIONS:
        annotations = {}
        for report_annotation in report_out[REPORT_ANNOTATIONS]:
            annotations[report_annotation["name"]] = report_annotation["value"]

        return annotations

    return report_out[info_type]


def get_report_annotations(report_path):
    annotations = _get_report_info(report_path,REPORT_ANNOTATIONS,"","")
    print("[INFO] report annotations : %s" % annotations)
    return annotations

def get_report_results(report_path, profile_type, profile_version):
    results = _get_report_info(report_path,REPORT_RESULTS,profile_type,profile_version)
    print("[INFO] report results : %s" % results)
    results["failed"] = int(results["failed"])
    results["passed"] = int(results["passed"])
    return results
    
def get_report_digests(report_path):
    digests = _get_report_info(report_path,REPORT_DIGESTS,"","")
    print("[INFO] report digests : %s" % digests)
    return digests

def get_report_metadata(report_path):
    metadata = _get_report_info(report_path,REPORT_METADATA,"","")
    print("[INFO] report metadata : %s" % metadata)
    return metadata

def get_report_chart_url(report_path):
     metadata = _get_report_info(report_path,REPORT_METADATA,"","")
     print("[INFO] report chart-uri : %s" % metadata["chart-uri"])
     return metadata["chart-uri"]

def get_report_chart(report_path):
     metadata = _get_report_info(report_path,REPORT_METADATA,"","")
     print("[INFO] report chart : %s" % metadata["chart"])
     return metadata["chart"]




