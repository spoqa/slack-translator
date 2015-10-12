import os

from flask import Flask, jsonify, request
from flask.ext.cache import Cache
import requests


app = Flask(__name__)

if 'REDIS_URL' in os.environ:
    cache = Cache(app, config={
        'CACHE_TYPE': 'redis',
        'CACHE_KEY_PREFIX': 'slack-translator',
        'CACHE_REDIS_URL': os.environ['REDIS_URL']
    })
else:
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})


@cache.memoize(timeout=86400)
def translate(text, from_, to):
    return requests.get(
        'https://www.googleapis.com/language/translate/v2',
        params=dict(
            format='text',
            key=os.environ['GOOGLE_API_KEY'],
            q=text,
            source=from_, target=to
        )
    ).json()['data']['translations'][0]['translatedText']


@cache.memoize(timeout=86400)
def get_user(user_id):
    return requests.get(
        'https://slack.com/api/users.info',
        params=dict(
            token=os.environ['SLACK_API_TOKEN'],
            user=user_id
        )
    ).json()['user']


@app.route('/<string:from_>/<string:to>', methods=['GET', 'POST'])
def index(from_, to):
    translated = translate(request.values.get('text'), from_, to)
    user = get_user(request.values.get('user_id'))

    for txt in (request.values.get('text'), translated):
        response = requests.post(
            os.environ['SLACK_WEBHOOK_URL'],
            json={
                "username": request.values['user_name'],
                "text": txt,
                "mrkdwn": True,
                "parse": "full",
                "channel": '#'+request.values['channel_name'],
                "icon_url": user['profile']['image_72']
            }
        )
    return response.text


if __name__ == '__main__':
    app.run(debug=True)
