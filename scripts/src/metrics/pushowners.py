import argparse
import re
from github import Github
import yaml
import sys
import analytics
sys.path.append('../')
from owners import owners_file

def process_pr(added_file,modified_file):
    users_included=""
    provider_delivery=""
    vendor_name=""
    chart_name=""
    vendor_type=""
    action=""
    update=""
    if modified_file!='':
        action="update"
        update="existing-vendor"
        users_included,provider_delivery,vendor_name,chart_name,vendor_type=owners_file.getFileContent(modified_file)
    elif added_file!='':
        action="create"
        update="new-vendor"
        users_included,provider_delivery,vendor_name,chart_name,vendor_type=owners_file.getFileContent(added_file)
    return users_included,provider_delivery,vendor_name,chart_name,vendor_type,action,update


def send_owner_metric(write_key,prefix,users_included,provider_delivery,partner,chart_name,type,action,update):
    if chart_name!="" and partner!="":
        id = f"{prefix}-{type}-{chart_name}"
        properties = { "type" : type, "vendor": partner, "chart" : chart_name, "users_included" : users_included, "provider_delivery" :provider_delivery, "action" : action, "update" : update}
        send_metric(write_key,id,"owners v1.0",properties)

def on_error(error,items):
    print("An error occurred creating metrics:", error)
    print("error with items:",items)
    sys.exit(1)

def send_metric(write_key,id,event,properties):

    analytics.write_key = write_key
    analytics.on_error = on_error

    print(f'[INFO] Add track:  id: {id},  event:{event},  properties:{properties}')

    analytics.track(id, event, properties)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--write-key", dest="write_key", type=str, required=True,
                        help="segment write key")
    parser.add_argument("-t", "--metric-type", dest="type", type=str, required=True,
                        help="metric type, releases or pull_request")
    parser.add_argument("-n", "--added", dest="added", nargs="*", required=False,
                        help="files added")
    parser.add_argument("-a", "--modified", dest="modified", nargs="*", required=False,
                        help="files modified")
    parser.add_argument("-r", "--repository", dest="repository", type=str, required=False,
                        help="The repository of the pr")
    parser.add_argument("-p", "--prefix", dest="prefix", type=str, required=False,
                        help="The prefix of the id in segment")


    args = parser.parse_args()
    print("Input arguments:")
    print(f"   --write-key length : {len(args.write_key)}")
    print(f"   --metric-type : {args.type}")
    print(f"   --added : {args.added}")
    print(f"   --modified : {args.modified}")
    print(f"   --repository : {args.repository}")
    print(f"   --prefix : {args.prefix}")

    if not args.write_key:
        print("Error: Segment write key not set")
        sys.exit(1)

    users_included,provider_delivery,vendor_name,chart_name,vendor_type,action,update = process_pr(args.added[0],args.modified[0])
    send_owner_metric(args.write_key,args.prefix,users_included,provider_delivery,vendor_name,chart_name,vendor_type,action,update)

if __name__ == '__main__':
    main()