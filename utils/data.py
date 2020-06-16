import json

from collections import namedtuple

def get_json(file):
    """Get and parse a json file."""
    with open(file, encoding='utf8') as data:
        return json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
