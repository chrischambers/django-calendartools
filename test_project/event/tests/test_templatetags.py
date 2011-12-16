# -*- coding: UTF-8 -*-

from datetime import datetime, timedelta
from django.template import Template, Context
from django.test import TestCase
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from nose.tools import *
from calendartools.templatetags.calendartools_tags import (
    get_query_string,
    set_query_string,
    delete_query_string,
    clear_query_string,
    persist_query_string,
    time_relative_to_today,
    columns
)
from calendartools.periods import Day


class TestTranslationTags(TestCase):
    def setUp(self):
        translation.activate('ar')

    def tearDown(self):
        translation.deactivate()

    def test_no_trans(self):
        context = Context({
            'january': _('January')
        })
        template = Template("""
            {{ january }}
        """)
        output = template.render(context)
        assert_in(u'يناير', output)
        template = Template("""
            {% load calendartools_tags %}
            {% notrans %}{{ january }}{% endnotrans %}
        """)
        output = template.render(context)
        assert_not_in(u'يناير', output)
        assert_in('January', output)

    def test_no_trans_filter(self):
        context = Context({
            'january': _('January')
        })
        template = Template("""
            {{ january }}
        """)
        output = template.render(context)
        assert_in(u'يناير', output)
        template = Template("""
            {% load calendartools_tags %}
            {{ january|notrans }}
        """)
        output = template.render(context)
        assert_not_in(u'يناير', output)
        assert_in('January', output)


class TestQueryStringManipulation(TestCase):
    def setUp(self):
        self.urls = (
            'http://example.com/foo',
            'http://example.com/foo/',
            'http://example.com/foo/?a=1&b=2',
            'http://example.com/foo/?a=1&a=4&b=2&b=5',
            '/foo',
            '/foo/',
            '/foo/?a=1&b=2',
            '/foo/?a=1&a=4&b=2&b=5',
        )

    def test_clear_query_string(self):
        expected = (
            'http://example.com/foo',
            'http://example.com/foo/',
            'http://example.com/foo/',
            'http://example.com/foo/',
            '/foo',
            '/foo/',
            '/foo/',
            '/foo/',
        )

        for url, expected in zip(self.urls, expected):
            assert_equal(clear_query_string(url), expected)

    def test_set_query_string(self):
        mapping = (
            ('http://example.com/foo',            'a', 1,
             'http://example.com/foo?a=1'),
            ('http://example.com/foo/',           'a', 1,
             'http://example.com/foo/?a=1'),
            ('http://example.com/foo/?a=2',       'a', 1,
             'http://example.com/foo/?a=1'),
            ('http://example.com/foo/?a=2&b=2&b=5', 'a', 1,
             'http://example.com/foo/?a=1&b=2&b=5'),
            ('http://example.com/foo/?b=2&a=2&c=4&b=5', 'a', 1,
             'http://example.com/foo/?a=1&b=2&b=5&c=4'),
            ('/foo',            'a', 1,
             '/foo?a=1'),
            ('/foo/',           'a', 1,
             '/foo/?a=1'),
            ('/foo/?a=2',       'a', 1,
             '/foo/?a=1'),
            ('/foo/?a=2&b=2&b=5', 'a', 1,
             '/foo/?a=1&b=2&b=5'),
        )
        for url, key, value, expected in mapping:
            assert_equal(set_query_string(url, key, value), expected)

    def test_get_query_string(self):
        mapping = (
            ('http://example.com/foo',  'a', ''),
            ('http://example.com/foo/', 'a', ''),
            ('http://example.com/foo/?a=2', 'a', ['2'],),
            ('http://example.com/foo/?a=2&a=4&b=2&b=5', 'a', ['2','4']),
            ('/foo',  'a', ''),
            ('/foo/', 'a', ''),
            ('/foo/?a=2', 'a', ['2'],),
            ('/foo/?a=2&a=4&b=2&b=5', 'a', ['2','4']),
        )
        for url, key, expected in mapping:
            assert_equal(get_query_string(url, key), expected)

    def test_delete_query_string(self):
        mapping = (
            ('http://example.com/foo',  'a',
             'http://example.com/foo'),
            ('http://example.com/foo/', 'a',
             'http://example.com/foo/'),
            ('http://example.com/foo/?a=2', 'a',
             'http://example.com/foo/',),
            ('http://example.com/foo/?a=2&a=4&b=2&b=5', 'a',
             'http://example.com/foo/?b=2&b=5'),
            ('http://example.com/foo/?a=2&a=4&c=2&b=5', 'a',
             'http://example.com/foo/?b=5&c=2'),
            ('/foo',  'a',
             '/foo'),
            ('/foo/', 'a',
             '/foo/'),
            ('/foo/?a=2', 'a',
             '/foo/',),
            ('/foo/?a=2&a=4&b=2&b=5', 'a',
             '/foo/?b=2&b=5'),
        )
        for url, key, expected in mapping:
            assert_equal(delete_query_string(url, key), expected)

    def test_persist_query_string(self):
        from_url = 'http://foo.com/flub/index.html?a=1&b=2&c=3'
        mapping = (
            ('/?a=foo',          '/?a=foo&b=2&c=3'),
            ('/?d=4',            '/?a=1&b=2&c=3&d=4'),
            ('/?b=bar&d=bing',   '/?a=1&b=bar&c=3&d=bing'),
            ('/zub/?b=a&d=b',    '/zub/?a=1&b=a&c=3&d=b'),
        )
        for url, expected_result in mapping:
            assert_equal(persist_query_string(url, from_url), expected_result)

class TestTimeRelativeToToday(TestCase):
    def setUp(self):
        now = datetime.now()
        first_thing = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_thing = (first_thing + timedelta(1)) - timedelta.resolution

        yesterday = first_thing - timedelta.resolution
        last_week = first_thing - timedelta(7)

        tomorrow = last_thing + timedelta.resolution
        next_week = first_thing + timedelta(7)

        self.mapping = [
            (now,         'today'),
            (first_thing, 'today'),
            (last_thing,  'today'),
            (Day(now),    'today'),
            (yesterday,   'past'),
            (last_week,   'past'),
            (tomorrow,    'future'),
            (next_week,   'future'),
        ]

    def test_time_relative_to_today(self):
        for dt, expected in self.mapping:
            assert_equal(time_relative_to_today(dt), expected)


class TestColumns(TestCase):
    def setUp(self):
        self.odd_list = range(9)
        self.even_list = range(10)

    def test_columns_no_padding(self):
        assert_equal(
            columns(self.odd_list, 2, pad_columns=False),
            [[0,1,2,3,4], [5,6,7,8]]
        )
        assert_equal(
            columns(self.even_list, 2, pad_columns=False),
            [[0,1,2,3,4], [5,6,7,8,9]]
        )

    def test_columns_padding(self):
        assert_equal(
            columns(self.odd_list, 2),
            [[0,1,2,3,4], [5,6,7,8,None]]
        )
        assert_equal(
            columns(self.even_list, 3, filler='foo'),
            [[0,1,2,3], [4,5,6,7], [8,9,'foo','foo']]
        )
