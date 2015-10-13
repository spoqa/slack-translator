# -*- coding: utf-8 -*-
from app import get_user, translate


def test_translate():
    assert translate(u'테스트', 'ko', 'ja') == u'テスト'
    assert translate(u'テスト', 'ja', 'ko') == u'테스트'


def test_formatted_text_translate():
    assert translate(u'<테스트>', 'ko', 'ja') == u'<テスト>'


def test_get_user():
    get_user('U024SNTB4')['profile']['first_name'] == u'JC'
