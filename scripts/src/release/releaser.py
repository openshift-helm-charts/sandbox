"""
schedule:
    - cron: "0 0 * * *"

'schedule': [{'cron': '0 0 * * *'}]
"""
import yaml
import os
import argparse
import sys
from release import release_info
from git import Repo

sys.path.append('../')
from github import gitutils

SCHEDULE_YAML_FILE=".github/workflows/schedule.yml"
BUILD_YAML_FILE=".github/workflows/build.yml"

RELEASE_INFO_FILE="release/release_info.json"


def update_workflow():

    data = {}
    with open(SCHEDULE_YAML_FILE,'r') as yaml_file:
        data = yaml.full_load(yaml_file)

    new_yaml_snippet = {'schedule': [{'cron': '0 0 * * * '}]}
    data[True].update(new_yaml_snippet)

    print(f"add cron job in {os.getcwd()}/{SCHEDULE_YAML_FILE}")

    with open(SCHEDULE_YAML_FILE,'w') as updated_yaml_file:
        yaml.safe_dump(data, updated_yaml_file)

    with open(BUILD_YAML_FILE,'r') as yaml_file:
        data = yaml.full_load(yaml_file)

    verifier_image = data["jobs"]["chart-certification"]["env"]["VERIFIER_IMAGE"]
    data["jobs"]["chart-certification"]["env"]["VERIFIER_IMAGE"] = verifier_image.replace('chart-verifier:main','chart-verifier:latest')
    print(f"change verifier image with: {data['jobs']['chart-certification']['env']['VERIFIER_IMAGE']}")

    with open(BUILD_YAML_FILE,'w') as updated_yaml_file:
        yaml.safe_dump(data, updated_yaml_file)

def get_release_info(directory):

    data = {}
    print(f"read file: {directory}{RELEASE_INFO_FILE}")
    with open(f"{directory}{RELEASE_INFO_FILE}",'r') as json_file:
        data = json.load(json_file)
    return data


def make_required_changes(release_info_dir,origin,destination):

    print(f"Make required changes from {origin} to {destination}")

    repository = "development"
    if "charts" in origin or "development" in destination:
        repository = "charts"

    replaces = release_info.get_replaces(repository,release_info_dir)

    for replace in replaces:
        replace_this=f"{destination}{replace}"
        with_this = f"{origin}{replace}"
        if os.path.isdir(replace_this):
            print(f"Replace directory {replace_this} with {with_this}")
            os.system(f"rm -rf {replace_this}")
            os.system(f"cp -r {with_this} {replace_this}")
        else:
            print(f"Replace file {replace_this} with {with_this}")
            os.system(f"cp {with_this} {replace_this}")

    merges =  release_info.get_merges(repository,release_info_dir)

    for merge in merges:
        merge_this = f"{origin}{merge}"
        into_this = f"{destination}{merge}"

        if os.path.isdir(merge_this):
            print(f"Merge directory {merge_this} with {into_this}")
            os.system(f"rsync -r {merge_this}/ {into_this}/")
        else:
            print(f"Merge file {merge_this} with {into_this}")
            os.system(f"cp {merge_this} {into_this}")


    ignores = release_info.get_ignores(repository,release_info_dir)
    for ignore in ignores:
        ignore_this = f"{destination}{ignore}"
        if os.path.isdir(ignore_this):
            print(f"Ignore/delete directory {ignore_this}")
            os.system(f"rm -rf {ignore_this}")
        else:
            print(f"Ignore/delete file {ignore_this}")
            os.system(f"rm {ignore_this}")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--version", dest="version", type=str, required=True,
                        help="Version to compare")
    parser.add_argument("-d", "--development_dir", dest="dev_dir", type=str, required=True,
                       help="Directory of development code with latest release info.")
    parser.add_argument("-c", "--charts_dir", dest="charts_dir", type=str, required=True,
                        help="Directory of charts code.")
    args = parser.parse_args()

    start_directory = os.getcwd()

    print(f"make changes to charts from development")
    make_required_changes(args.dev_dir,args.dev_dir,args.charts_dir)
    print(f"make changes to development from charts")
    make_required_changes(args.dev_dir,args.charts_dir,args.dev_dir)
    print(f"edit files in charts")
    os.chdir(args.charts_dir)
    update_workflow()
    print(f"create charts pull request")

    gitutils.create_charts_pr(args.version)

    os.chdir(start_directory)
    print(f"commit development changes")
    gitutils.commit_development_updates(args.version)

if __name__ == "__main__":
    main()