
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

def send_release_metrics(write_key, downloads):
    metrics={}
    for release in downloads:
        _,provider,chart,_ = index.get_chart_info(release.get('name'))
        if len(provider)>0:
            if provider not in metrics:
                metrics[provider] = {}
            if chart not in metrics[provider]:
                metrics[provider][chart] = {}

            for key in release.get('asset'):
                metrics[provider][chart][key] = release.get('asset')[key]


    for provider in metrics:
        for chart in metrics[provider]:
            send_metric(write_key,provider,f"{chart} downloads", metrics[provider][chart])


def send_fail_metric(write_key,partner,chart,message):

    properties = { "chart" : chart, "message" : message }

    send_metric(write_key,partner,"PR run Failed",properties)

def send_pass_metric(write_key,partner,chart):

    properties = { "chart" : chart }

    send_metric(write_key,partner,"PR Success",properties)


def on_error(error,items):
    print("An error occurred creating metrics:", error)
    print("error with items:",items)
    sys.exit(1)


def send_metric(write_key,partner,event,properties):

    analytics.write_key = write_key
    analytics.on_error = on_error

    logging.info(f'Add track:  user: {partner},  event:{event},  properties:{properties}')

    analytics.track(partner, event, properties)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--write-key", dest="write_key", type=str, required=True,
                        help="segment write key")
    parser.add_argument("-t", "--metric-type", dest="type", type=str, required=True,
                        help="metric type, releases or pull_request")
    parser.add_argument("-c", "--chart", dest="chart", type=str, required=False,
                        help="chart name for metric")
    parser.add_argument("-p", "--partner", dest="partner", type=str, required=False,
                        help="name of partner")
    parser.add_argument("-m", "--message", dest="message", type=str, required=False,
                        help="message for metric")
    args = parser.parse_args()

    if not args.write_key:
        print("Error: Segment write key not set")
        sys.exit(1)

    if args.type == "pull_request":
        if args.message:
            send_fail_metric(args.write_key,args.partner,args.chart,args.message)
        else:
            send_pass_metric(args.write_key,args.partner,args.chart)
    else:
        send_release_metrics(args.write_key,get_release_metrics())


if __name__ == '__main__':
    main()
