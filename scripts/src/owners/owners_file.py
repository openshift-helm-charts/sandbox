import os

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_owner_data(category, organization, chart):
    try:
        with open(os.path.join("charts", category, organization, chart, "OWNERS")) as owner_data:
            owner_content = yaml.load(owner_data,Loader=Loader)
        return True,owner_content
    except Exception as err:
        print(f"Exception loading OWNERS file: {err}")
        return False,""


def get_provider_delivery(owner_data):
    provider_delivery = False
    try:
        provider_delivery = owner_data["providerDelivery"]
    except Exception:
        pass
    return provider_delivery

def getFileContent(changed_file):
    users_included="No"
    provider_delivery="No"
    vendor_name=""
    chart_name=""
    vendor_type=""
    with open(changed_file) as file:
        documents = yaml.full_load(file)
        for key, value in documents.items():
            if key=='providerDelivery' and value=='True':
                provider_delivery="Yes"
            elif key=='users' and len(key)!=0:
                users_included="Yes"
            elif key=='vendor':
                vendor_name=value['name']
            elif key=='chart':
                chart_name=value['name']
        path_as_list=changed_file.split("/")
        for i in (range(len(path_as_list) - 1)):
            if path_as_list[i]=='charts':
                vendor_type=path_as_list[i+1]
    return users_included,provider_delivery,vendor_name,chart_name,vendor_type

