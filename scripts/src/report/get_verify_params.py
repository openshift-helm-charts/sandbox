
import os
sys.path.append('../')
from chartprreview import chartprreview

def generate_verify_options(directory,category, organization, chart, version):
    print("[INFO] Generate verify options. %s, %s, %s" % (organization,chart,version))
    src = os.path.join(os.getcwd(), "charts", category, organization, chart, version, "src")
    report_path = os.path.join("charts", category, organization, chart, version, "report.yaml")
    tar = os.path.join("charts", category, organization, chart, version, f"{chart}-{version}.tgz")

    vendor_type = chartprreview.get_vendor_type(directory)
    flags = f"--set profile.vendortype={vendor_type}"
    cluster_required = True
    if os.path.exists(report_path):
        flags = f"{flags} -e has_readme"
        cluster_required = False

    if os.path.exists(src) and not os.path.exists(src):
        return flags,src,True,cluster_required
    elif os.path.exists(tar) and not os.path.exists(src):
        return flags,tar,True,cluster_required
    elif os.path.exists(tar) and os.path.exists(src):
        msg = "[ERROR] Both chart source directory and tarball should not exist"
        chartprreview.write_error_log(directory, msg)
        sys.exit(1)
    else:
        return "","",False,False



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--api-url", dest="api_url", type=str, required=True,
                        help="API URL for the pull request")
    parser.add_argument("-d", "--directory", dest="directory", type=str, required=True,
                        help="artifact directory for archival")

    args = parser.parse_args()

    category, organization, chart, version = chartprreview.get_modified_charts(args.directory, args.api_url)

    flags,chart_uri,report_needed,cluster_needed = generate_verify_options(args.directory,category, organization, chart, version)
    if not report_needed:
        print(f"::set-output name=report_needed::false")
        print(f"::set-output name=cluster_needed::false")
    else:
        print(f"::set-output name=report_needed::true")
        print(f"::set-output name=verify_args::{flags}")
        print(f"::set-output name=verify_uri::{chart_uri}")
        if cluster_needed:
            print(f"::set-output name=cluster_needed::true")
        else:
            print(f"::set-output name=cluster_needed::false")

