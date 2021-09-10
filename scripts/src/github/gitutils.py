import os
import json
import requests
import git
from git import Repo
from git.exc import GitCommandError

GITHUB_BASE_URL = 'https://api.github.com'
#CHARTS_REPO = 'openshift-helm-charts/charts'
#DEVELOPMENT_REPO = 'openshift-helm-charts/development'
CHARTS_REPO = 'mmulholla/charts'
DEVELOPMENT_REPO = 'mmulholla/development'
#CHARTS_REPO = 'openshift-helm-charts/sandbox'

# GitHub actions bot email for git email
GITHUB_ACTIONS_BOT_EMAIL = 'mmulholl@redhat.com'

def set_git_username_email(repo, username, email):
    """
    Parameters:
    repo (git.Repo): git.Repo instance of the local directory
    username (str): git username to set
    email (str): git email to set
    """
    repo.config_writer().set_value("user", "name", username).release()
    repo.config_writer().set_value("user", "email", email).release()


def github_api_post(endpoint, bot_token, headers={}, json={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.post(f'{GITHUB_BASE_URL}/{endpoint}',
                      headers=headers, json=json)

    return r

def github_api_get(endpoint, bot_token, headers={}):
    if not headers:
        headers = {'Accept': 'application/vnd.github.v3+json',
                   'Authorization': f'Bearer {bot_token}'}
    r = requests.get(f'{GITHUB_BASE_URL}/{endpoint}', headers=headers)

    return r

def github_api(method, endpoint, bot_token, headers={}, data={}, json={}):
    if method == 'get':
        return github_api_get(endpoint, bot_token, headers=headers)
    elif method == 'post':
        return github_api_post(endpoint, bot_token, headers=headers, json=json)
    else:
        raise ValueError(
            f"Github API method {method} not implemented in helper function")

def get_bot_name_and_token():
    bot_name = os.environ.get("BOT_NAME")
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_name and not bot_token:
        print("bot name and token not found use GITHUB_TOKEN")
        bot_name = "github-actions[bot]"
        bot_token = os.environ.get("GITHUB_TOKEN")
        if not bot_token:
            raise Exception("BOT_TOKEN environment variable not defined")
    elif not bot_name:
        raise Exception("BOT_TOKEN set but BOT_NAME not specified")
    elif not bot_token:
        raise Exception("BOT_NAME set but BOT_TOKEN not specified")
    else:
        print(f"found bot name ({bot_name}) and token: ")
    return bot_name, bot_token


def create_charts_pr(version):

    repo = Repo(os.getcwd())

    bot_name, bot_token = get_bot_name_and_token()
    set_git_username_email(repo,bot_name,GITHUB_ACTIONS_BOT_EMAIL)

    branch_name = f"Release-{version}"
    repo.create_head(branch_name)
    print(f"checkout branch {branch_name}")
    repo.git.checkout(branch_name)

    changed = [ item.a_path for item in repo.index.diff(None) ]
    for change in changed:
        print(f"Add file: {change}")
        repo.git.add(change)

    print(f"commit changes with message: {branch_name}")
    repo.index.commit(branch_name)

    print(f"get existing branches: {branch_name}")
    r = github_api(
        'get', f'repos/{CHARTS_REPO}/branches', bot_token)

    branches = json.loads(r.text)
    branch_names = [branch['name'] for branch in branches]
    print(f"Existing branches : {branch_names}")

    print(f"push the branch to {CHARTS_REPO}")
    repo.git.push(f'https://x-access-token:{bot_token}@github.com/{CHARTS_REPO}',
               f'HEAD:refs/heads/{branch_name}','-f')

    print("make the pull request")
    data = {'head': branch_name, 'base': 'main',
            'title': branch_name, 'body': branch_name}

    r = github_api(
        'post', f'repos/{CHARTS_REPO}/pulls', bot_token, json=data)
    j = json.loads(r.text)
    print(f"pull request number: {j['number']} ")


def commit_development_updates(version):

    repo = Repo(os.getcwd())

    print("checkout main")
    repo.git.checkout("main")

    changed = [ item.a_path for item in repo.index.diff(None) ]
    for change in changed:
        print(f"Add file: {change}")
        git.add(change)

    print(f"commit changes with message: Version-{version}")
    repo.index.commit(f"Version-{version} Update charts from chart repository")

    print(f"push the branch to {DEVELOPMENT_REPO}")
    bot_name, bot_token = get_bot_name_and_token()

    repo.git.push(f'https://x-access-token:{bot_token}@github.com/{DEVELOPMENT_REPO}',
                  f'HEAD:refs/heads/main', '-f')
