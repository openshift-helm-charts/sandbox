import os
import requests
import logging
import sys

logging.basicConfig(level=logging.INFO)


def parse_response(response):
    result = []
    for obj in response:
        if 'name' in obj and len(obj.get('assets', [])) > 0:
            release = {
                'name': obj['name'],
                'assets': list(map(lambda asset: (asset.get('name', 'unknown'), asset.get('download_count', 0)), obj['assets']))
            }
            result.append(release)
    return result


def get_metrics():
    response = requests.get(
        'https://api.github.com/repos/openshift-helm-charts/charts/releases')
    if response.status_code != 200:
        logging.error(f"expect reponse 200, got {response.status_code}")
        sys.exit(1)
    return parse_response(response.json())


def send_metrics(metrics: dict):
    for release in metrics:
        headers = {
            'Authorization': os.getenv('SEGMENT_WRITE_KEY')}
        json = {
            "userId": release['name'],
            "event": "Chart Certification Metrics",
            "properties": dict(release['assets']),
        }
        response = requests.post(
            url='https://api.segment.io/v1/track', headers=headers, json=json)
        if response.status_code != 200:
            logging.error(f"expect reponse 200, got {response.status_code}")
            sys.exit(1)
        logging.info(f'POST {json["userId"]}\nRESPONSE {response}')


def main():
    send_metrics(get_metrics())


if __name__ == '__main__':
    main()
