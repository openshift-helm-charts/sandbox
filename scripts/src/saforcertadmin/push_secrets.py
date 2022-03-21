from base64 import b64encode
from nacl import encoding, public
import logging
import os
import sys
import requests
import argparse

token = os.environ.get("GITHUB_TOKEN")
headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}

logging.basicConfig(level=logging.INFO)

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def get_repo_public_key(repo):
    response = requests.get(f'https://api.github.com/repos/{repo}/actions/secrets/public-key', headers=headers)
    if response.status_code != 200:
        logging.error(f"unexpected response getting repo public key : {response.status_code} : {response.reason}")
        sys.exit(1)
    response_json = response.json()
    return response_json['key_id'], response_json['key']

def get_repo_secrets(repo):
    secret_names = []
    response = requests.get(f'https://api.github.com/repos/{repo}/actions/secrets', headers=headers)
    if response.status_code != 200:
        logging.error(f"unexpected response getting secrets : {response.status_code} : {response.reason}")
        sys.exit(1)
    response_json = response.json()
    for i in range(response_json['total_count']):
        secret_names.append(response_json['secrets'][i]['name'])
    return secret_names

def create_or_update_repo_secrets(repo, secret_name, key_id, encrypted_value):
    response = requests.put(f'https://api.github.com/repos/{repo}/actions/secrets/{secret_name}', json={'key_id': key_id, 'encrypted_value': encrypted_value}, headers=headers)
    if response.status_code != 200 and response.status_code != 204:
        logging.error(f"unexpected response during put request : {response.status_code} : {response.reason}")
        sys.exit(1)
    #response_json = response.json()
    logging.info('Secret create or update successful')

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo", dest="repo", type=str, required=True,
                                        help="Github repo name in {org}/{repo_name} format")
    parser.add_argument("-l", "--list", dest="list", action='store_true', required=False,
                                        help="List the secret names")
    parser.add_argument("-s", "--secret", dest="secret", type=str, required=False,
                                        help="Secret name")
    parser.add_argument("-v", "--value", dest="value", type=str, required=False,
                                        help="Secret value to set")
    args = parser.parse_args()

    if args.list:
        secrets = get_repo_secrets(args.repo)
        logging.info(f'Github Secret Names: {secrets}')
    elif args.secret and args.value:
        secret_name = args.secret
        secret_value = args.value
        logging.info(f'Setting SECRET: {secret_name} with VALUE: {secret_value}')
        key_id, public_key = get_repo_public_key(args.repo)
        encrypted_value = encrypt(public_key, secret_value)
        create_or_update_repo_secrets(args.repo, secret_name, key_id, encrypted_value)
    else:
        logging.error('Wrong argument combination')

if __name__ == '__main__':
    main()
