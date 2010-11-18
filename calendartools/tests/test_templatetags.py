# -*- coding: UTF-8 -*-

from django.template import Template, Context
from django.test import TestCase
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from nose.tools import *

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
