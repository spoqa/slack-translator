# -*- coding: utf-8 -*-
from app import get_user, translate


def test_translate():
    assert translate(u'테스트', 'ko', 'ja') == u'テスト'
    assert translate(u'テスト', 'ja', 'ko') == u'테스트'


def test_formatted_text_translate():
    assert translate(u'<테스트>', 'ko', 'ja') == u'<テスト>'


def test_get_user():
    get_user('U024SNTB4')['profile']['first_name'] == u'JC'


def test_app(fx_app):
    assert 'ok' in fx_app.post('/ko/ja', data=dict(
        text=u'테스트',
        user_id='U024SNTB4',
        user_name='jc',
        channel_name='slack-translator-test'
    )).data
