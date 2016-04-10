# -*- coding: utf-8 -*-
from app import get_user, make_app, translate


def test_translate(fx_app):
    with fx_app.test_request_context():
        assert translate(u'테스트', 'ko', 'ja') == u'テスト'
        assert translate(u'テスト', 'ja', 'ko') == u'테스트'


def test_formatted_text_translate(fx_app):
    with fx_app.test_request_context():
        assert translate(u'<테스트>', 'ko', 'ja') == u'<テスト>'


def test_get_user(fx_app):
    with fx_app.test_request_context():
        get_user('U024SNTB4')['profile']['first_name'] == u'JC'


def test_make_app():
    app = make_app({
        'DEBUG': 'YES',
        'REDIS_URL': 'NO_URL'
    })

    assert app.config['CELERY_ALWAYS_EAGER']


def test_make_app_async():
    app = make_app({
        'DEBUG': 'YES',
        'ASYNC_TRANSLATION': 'YES',
        'REDIS_URL': 'NO_URL'
    })

    assert not app.config['CELERY_ALWAYS_EAGER']


def test_app(fx_app_client):
    assert 'ok' in str(fx_app_client.post('/ko/ja', data=dict(
        text=u'테스트',
        user_id='U024SNTB4',
        user_name='jc',
        channel_name='slack-translator-test'
    )).data)
