import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


profiles_base_url = "https://raw.githubusercontent.com/redhat-certification/chart-verifier"

def get_mandatory_checks(verifier_version,profileType,profileVersion):

    profile_url = f"{profiles_base_url}/{verifier_version}/config/profile-{profileType}-{profileVersion}.yaml"

    print(f"get {profile_url}")

    response = requests.get(profile_url)

    mandatary_checks = []
    if response.status_code == 200:

        print(f"response: {response.text}")

        profile_content = yaml.load(response.text, Loader=Loader)

        checks = profile_content["checks"]

        for check in checks:
            if check["type"] == "Mandatory":
                mandatary_checks.append(check["name"])
    else:
        return False,f"[ERROR] bad response loading profile {profile_url} : {response.status_code}"

    return True,mandatary_checks







