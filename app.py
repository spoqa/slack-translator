import os

from celery import Celery
from flask import Flask, request
from flask.ext.cache import Cache
import requests


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def make_app(env):
    app = Flask(__name__)
    app.debug = 'DEBUG' in os.environ
    app.config.update(BROKER_URL=env['REDIS_URL'],
                      CELERY_RESULT_BACKEND=env['REDIS_URL'])
    async = ('ASYNC_TRANSLATION' in env and
             env['ASYNC_TRANSLATION'] == 'YES')
    app.config.update(CELERY_ALWAYS_EAGER=(False if async else True))
    return app


def make_cache(app):
    try:
        cache = Cache(app, config={
            'CACHE_TYPE': 'redis',
            'CACHE_KEY_PREFIX': 'slack-translator',
            'CACHE_REDIS_URL': app.config['BROKER_URL']
        })
    except KeyError:
        raise RuntimeError('REDIS_URL environment variable is required')
    return cache


app = make_app(os.environ)
cache = make_cache(app)
celery = make_celery(app)


@cache.memoize(timeout=86400)
def google_translate(text, from_, to):
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
def naver_translate(text, from_, to):
    response = requests.post(
        'https://openapi.naver.com/v1/language/translate',
        data=dict(
            text=text,
            source=from_, target=to
        ),
        headers={
            'X-Naver-Client-Id': os.environ['NAVER_CLIENT_ID'],
            'X-Naver-Client-Secret': os.environ['NAVER_CLIENT_SECRET']
        }
    )
    return response.json()['message']['result']['translatedText']


translate_engine = os.environ.get('TRANSLATE_ENGINE', 'google')
try:
    translate = globals()[translate_engine + '_translate']
except KeyError:
    raise RuntimeError(
        'TRANSLATE_ENGINE: there is no {0!r} translate engine'.format(
            translate_engine
        )
    )
assert callable(translate)


@cache.memoize(timeout=86400)
def get_user(user_id):
    return requests.get(
        'https://slack.com/api/users.info',
        params=dict(
            token=os.environ['SLACK_API_TOKEN'],
            user=user_id
        )
    ).json()['user']


@celery.task()
def translate_and_send(user_id, user_name, channel_name, text, from_, to):
    translated = translate(text, from_, to)
    user = get_user(user_id)

    for txt in (text, translated):
        response = requests.post(
            os.environ['SLACK_WEBHOOK_URL'],
            json={
                "username": user_name,
                "text": txt,
                "mrkdwn": True,
                "parse": "full",
                "channel": '#'+channel_name,
                "icon_url": user['profile']['image_72']
            }
        )
    return response.text


@app.route('/<string:from_>/<string:to>', methods=['GET', 'POST'])
def index(from_, to):
    translate_and_send.delay(
        request.values.get('user_id'),
        request.values.get('user_name'),
        request.values.get('channel_name'),
        request.values.get('text'),
        from_,
        to
    )
    return 'ok'


if __name__ == '__main__':
    app.run(debug=True)
