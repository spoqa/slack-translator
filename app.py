import os
import re

from celery import Celery
from flask import Flask, json, request
from flask.ext.cache import Cache
from redis import StrictRedis
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

redis_store = None
if 'REDIS_URL' in os.environ:
    redis_store = StrictRedis.from_url(os.environ['REDIS_URL'])


def store_to_redis(key, obj):
    """Save json-serializable object to redis"""
    if not redis_store:
        raise Exception('Please set `REDIS_URL` environment variable.')
    redis_store.set(key, json.dumps(obj))


def load_from_redis(key):
    """Load json-serializable object from redis"""
    if not redis_store:
        raise Exception('Please set `REDIS_URL` environment variable.')
    obj_raw = redis_store.get(key)
    if obj_raw is None:
        return None
    return json.loads(obj_raw)


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


def post_to_slack(**kwargs):
    """Post to slack"""

    return requests.post(
        os.environ['SLACK_WEBHOOK_URL'],
        json={
            # Set some sane defaults
            'mrkdwn': True,
            'parse': 'full',
            **kwargs
        }
    )


def post_to_slack_as_bot(channel_id, text):
    """Post to slack as slack-translator bot"""

    return post_to_slack(
        text=text,
        username='Slack Translator',
        channel=channel_id,
        icon_emoji=':globe_with_meridians:',
    )


def post_to_slack_as_user(user_id, channel_id, text):
    """Post to slack imitating a user"""
    user = get_user(user_id)

    return post_to_slack(
        text=text,
        username=user['name'],
        channel=channel_id,
        icon_url=user['profile']['image_72'],
    )


re_korean = re.compile('[가-힣ㄱ-ㅎ]')
re_japanese = re.compile('[ぁ-んァ-ン一-龯]')


def detect_language(text):
    """Detect language of given text. Only supports ko/ja/en."""
    korean_score = sum(bool(re_korean.match(c)) for c in text)
    japanese_score = sum(bool(re_japanese.match(c)) for c in text)
    if korean_score and korean_score >= japanese_score:
        return 'ko'
    if japanese_score > korean_score:
        return 'ja'
    return 'en'


def get_meeting_mode_channels():
    """Load meeting mode channels"""
    meeting_mode_channels = load_from_redis('meeting_mode_channels')
    if meeting_mode_channels is None:
        meeting_mode_channels = {}
        store_to_redis('meeting_mode_channels', meeting_mode_channels)
    return meeting_mode_channels


@app.route('/meeting_mode', methods=['POST'])
def meeting_mode():
    """Handle slack events"""
    if 'challenge' in request.json:
        # Handle Slack handler url verification
        return request.json['challenge']

    event = request.json.get('event', {})

    if 'bot_id' in event:
        # Ignore bot messages
        return ''

    meeting_mode_channels = get_meeting_mode_channels()

    channel_id = event.get('channel')
    text = event.get('text')
    user_id = event.get('user')

    if channel_id in meeting_mode_channels:
        lang1 = meeting_mode_channels[channel_id]['language1']
        lang2 = meeting_mode_channels[channel_id]['language2']
        if detect_language(text) == lang1:
            from_, to = lang1, lang2
        elif detect_language(text) == lang2:
            from_, to = lang2, lang1
        else:
            # Don't translate if language is undetected.
            return ''
        translated_text = translate(text, from_, to)

        post_to_slack_as_user(user_id, channel_id, translated_text)

    return ''


@app.route('/start_meeting_mode/<string:language1>/<string:language2>',
           methods=['GET', 'POST'])
def start_meeting_mode(language1, language2):
    """Start meeting mode. Translates all messages in `langauge1`
    and `language2` to each other.

    :param language1: Preferred language of the callee
    :param language2: Other language to translate
    """
    channel_id = request.values['channel_id']
    user_id = request.values['user_id']
    user_name = request.values['user_name']

    meeting_mode_channels = get_meeting_mode_channels()

    if channel_id in meeting_mode_channels:
        message = f'@{user_name}: 이미 회의 모드가 진행중입니다.'
        post_to_slack_as_bot(channel_id, message)
        return ''

    meeting_mode_channels[channel_id] = {
        'channel_id': channel_id,
        'user_id': user_id,
        'language1': language1,
        'language2': language2,
    }
    store_to_redis('meeting_mode_channels', meeting_mode_channels)
    message = f'@{user_name}님의 요청으로 회의 모드를 개시합니다. ' \
              f'현 시간부로 이 채널의 모든 대화는 번역됩니다.'
    post_to_slack_as_bot(channel_id, message)
    return ''


@app.route('/stop_meeting_mode/', methods=['GET', 'POST'])
def stop_meeting_mode():
    """Stops meeting mode in current channel"""
    channel_id = request.values['channel_id']
    user_name = request.values['user_name']
    meeting_mode_channels = get_meeting_mode_channels()

    if channel_id not in meeting_mode_channels:
        message = f'@{user_name}: 진행중인 회의 모드가 없습니다.'
        post_to_slack_as_bot(channel_id, message)
        return ''

    meeting_mode_channels.pop(channel_id)
    store_to_redis('meeting_mode_channels', meeting_mode_channels)

    message = f'@{user_name}님의 요청으로 회의 모드를 종료합니다.'
    post_to_slack_as_bot(channel_id, message)
    return ''


if __name__ == '__main__':
    app.run(debug=True)
