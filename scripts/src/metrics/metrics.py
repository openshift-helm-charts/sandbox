
import argparse
import itertools
import logging
import requests
import sys
import analytics
import os

sys.path.append('../')
from indexfile import index

logging.basicConfig(level=logging.INFO)

def parse_response(response):
    result = []
    for obj in response:
        if 'name' in obj and 'assets' in obj:
            for asset in obj['assets']:
                if asset["name"].endswith(".tgz"):
                    release = { 'name' : obj['name'], "asset" : { asset.get('name') : asset.get('download_count', 0)}}
                    result.append(release)
    return result


def get_release_metrics():
    result = []
    for i in itertools.count(start=1):
        response = requests.get(
            f'https://api.github.com/repos/openshift-helm-charts/charts/releases?per_page=100&page={i}')
        if not 200 <= response.status_code < 300:
            logging.error(f"unexpected response getting release data : {response.status_code} : {response.reason}")
            sys.exit(1)
        response_json = response.json()
        if len(response_json) == 0:
            break
        result.extend(response_json)
    return parse_response(result)


def send_release_metrics(metrics):
    for release in metrics:
        _,provider,chart,_ = index.get_chart_info(release.get('name'))
        if len(provider)>0:
            send_metric(provider,f"{chart} downloads", release.get('asset'))

def send_fail_metric(partner,chart,message):

    properties = { "chart" : chart, "message" : message }

    send_metric(partner,"PR run Failed",properties)

def send_pass_metric(partner,chart):

    properties = { "chart" : chart }

    send_metric(partner,"PR Success",properties)


def on_error(error,items):
    print("An error occurred creating metrics:", error)
    print("error with items:",items)
    sys.exit(1)


def send_metric(partner,event,properties):

    analytics.write_key = os.getenv('SEGMENT_WRITE_KEY')
    analytics.on_error = on_error

    analytics.track(partner, event, properties)

    logging.info(f'Add track:  user: {partner},  event:{event},  properties:{properties}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--metric-type", dest="type", type=str, required=True,
                        help="metric type, releases or pull_request")
    parser.add_argument("-c", "--chart", dest="chart", type=str, required=False,
                        help="chart name for metric")
    parser.add_argument("-p", "--partner", dest="partner", type=str, required=False,
                        help="name of partner")
    parser.add_argument("-m", "--message", dest="message", type=str, required=False,
                        help="message for metric")
    args = parser.parse_args()

    if not os.getenv('SEGMENT_WRITE_KEY'):
        print("Error SEGMENT_WRITE_KEY not found")
        sys.exit(1)

    if args.type == "pull_request":
        if args.message:
            send_fail_metric(args.partner,args.chart,args.message)
        else:
            send_pass_metric(args.partner,args.chart)
    else:
        send_release_metrics(get_release_metrics())


if __name__ == '__main__':
    main()
