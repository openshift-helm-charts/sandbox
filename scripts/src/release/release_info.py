"""
schedule:
    - cron: "0 0 * * *"

'schedule': [{'cron': '0 0 * * *'}]
"""
import json


RELEASE_INFO_FILE="release/release_info.json"

def _get_release_info(directory):

    if not directory:
        directory = "./"

    data = {}
    with open(f"{directory}{RELEASE_INFO_FILE}",'r') as json_file:
        data = json.load(json_file)

    return data

def get_version(directory):
    info = _get_release_info(directory)
    return info["version"]

def get_info(directory):
    info = _get_release_info(directory)
    return info["info"]


def get_replaces(repo,directory):
    info = _get_release_info(directory)
    if repo in info:
        if "replace" in info[repo]:
            return info[repo]["replace"]
    return []

def get_merges(repo,directory):
    info = _get_release_info(directory)
    if repo in info:
        if "merge" in info[repo]:
            return info[repo]["merge"]
    return []


def get_ignores(repo,directory):
    info = _get_release_info(directory)
    if repo in info:
        if "ignore" in info[repo]:
            return info[repo]["ignore"]
    return []


def main():

    print(f"[INFO] Version : {get_version('./')}")

    print(f"[INFO] Dev repo merges : {get_merges('development','./')}")

    print(f"[INFO] Dev repo replace : {get_replaces('development','./')}")

    print(f"[INFO] Dev repo ignore : {get_ignores('development','./')}")

    print(f"[INFO] Chart repo merges : {get_merges('charts','./')}")

    print(f"[INFO] Chart repo replace : {get_replaces('charts','./')}")

    print(f"[INFO] Chart repo ignore : {get_ignores('charts','./')}")


if __name__ == "__main__":
    main()