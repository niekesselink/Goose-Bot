import requests

URL = 'https://api.aidungeon.io'

TOKEN = None
CONFIG = None
MAX_RERUN = 5

def init_session(config):
    global TOKEN

    data = {}
    data['email'] = config.aid2.email
    data['password'] = config.aid2.password

    r = requests.post(f'{URL}/users', data)

    if not r.ok:
        print('/users', r.status_code, r.reason)
        return None

    try:
        TOKEN = r.json()['accessToken']
    except (ValueError, KeyError):
        print(f'{URL}/users: invalid response: {r.content}')

def read_config():
    global CONFIG

    r = requests.get(f'{URL}/sessions/*/config', headers={'X-Access-Token': TOKEN})

    if not r.ok:
        print('/sessions/*/config', r.status_code, r.reason)
    else:
        try:
            CONFIG = r.json()
        except ValueError:
            print(f'{URL}/sessions/*/config: invalid response: {r.content}')

def ready():
    return TOKEN is not None

def init_story(mode, character, name):
    data = {
        'storyMode': mode,
        'characterType': character,
        'name': name,
        'customPrompt': None,
        'promptId': None
    }

    r = None
    times = 0

    while (r is None or r.status_code >= 500) and times < MAX_RERUN:
        r = requests.post(f'{URL}/sessions', data, headers={'X-Access-Token': TOKEN})
        times += 1

    if not r.ok:
        print('/sessions', r.status_code, r.reason)
        return None, None
    else:
        try:
            r = r.json()
            return r['id'], r['story'][0]['value']
        except (ValueError, KeyError, IndexError):
            print(f'{URL}/sessions: invalid response: {r.content}')
            return None, None

def continue_story(story_id, text):
    data = {
        'text': text
    }

    r = None
    times = 0

    while (r is None or r.status_code >= 500) and times < MAX_RERUN:
        r = requests.post(f'{URL}/sessions/{story_id}/inputs', data, headers={'X-Access-Token': TOKEN})
        times += 1

    if not r.ok:
        print(f'/sessions/{story_id}/inputs', r.status_code, r.reason)
        return None, None
    else:
        try:
            r = r.json()
            return r[-1]['value']
        except (ValueError, KeyError, IndexError):
            print(f'{URL}/sessions/{story_id}/inputs: {r.content}')
            return None, None