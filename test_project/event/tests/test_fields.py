from django.test import TestCase
from nose.tools import *
from calendartools.fields import MultipleIntegerField


class TestMultipleIntegerField(TestCase):
    def setUp(self):
        self.field = MultipleIntegerField(
            [(1,'1'), (2, '2'), (3, '3')],
        )

    def test_clean(self):
        inputs = [
            (['1'], [1]),
            (['1', '3'], [1, 3]),
            (['3', '2', '1'], [3, 2, 1]),
        ]
        for inp, expected in inputs:
            assert_equal(self.field.clean(inp), expected)
