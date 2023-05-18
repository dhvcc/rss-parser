"""Unit tests in addition to doctests present."""
from datetime import datetime
from operator import eq, ge, gt, le, lt, ne
from random import randint
from typing import Optional

from rss_parser.models import RSSBaseModel
from rss_parser.models.types.tag import Tag


class Model(RSSBaseModel):
    number: Optional[Tag[int]]
    float_number: Optional[Tag[float]]
    string: Optional[Tag[str]]
    datetime: Optional[Tag[datetime]]


def rand_str():
    # FIXME: Yeah I know
    return "string"


def test_comparison_operators_number():
    number = randint(0, 2**32)  # noqa
    operator_result_list = [
        [eq, number, True],
        [eq, number + 1, False],
        [eq, number - 1, False],
        #
        [ne, number, False],
        [ne, number + 1, True],
        [ne, number - 1, True],
        #
        [gt, number, False],
        [gt, number + 1, False],
        [gt, number - 1, True],
        [gt, number - 0.1, True],
        #
        [lt, number, False],
        [lt, number + 1, True],
        [lt, number - 1, False],
        [lt, number + 0.1, True],
        #
        [ge, number, True],
        [ge, number + 1, False],
        [ge, number - 1, True],
        [ge, number - 0.1, True],
        #
        [le, number, True],
        [le, number + 1, True],
        [le, number - 1, False],
        [le, number + 0.1, True],
    ]
    obj = Model(number=number)

    for operator, b_operand, expected in operator_result_list:
        assert operator(obj.number, b_operand) is expected


def test_comparison_operators_float():
    number = float(randint(0, 2**32))  # noqa
    operator_result_list = [
        [eq, number, True],
        [eq, number + 1, False],
        [eq, number - 1, False],
        #
        [ne, number, False],
        [ne, number + 1, True],
        [ne, number - 1, True],
        #
        [gt, number, False],
        [gt, number + 1, False],
        [gt, number - 1, True],
        [gt, number - 0.1, True],
        #
        [lt, number, False],
        [lt, number + 1, True],
        [lt, number - 1, False],
        [lt, number + 0.1, True],
        #
        [ge, number, True],
        [ge, number + 1, False],
        [ge, number - 1, True],
        [ge, number - 0.1, True],
        #
        [le, number, True],
        [le, number + 1, True],
        [le, number - 1, False],
        [le, number + 0.1, True],
    ]
    # TODO: Investiagte why its mandatory to use camelCase from converter
    obj = Model(floatNumber=number)

    for operator, b_operand, expected in operator_result_list:
        assert operator(obj.float_number, b_operand) is expected


def test_comparison_operators_string():
    def add_to_last_char(s, n):
        return s[:-1] + chr(ord(s[-1]) + n)

    string = rand_str()
    operator_result_list = [
        [eq, string, True],
        [eq, string[:-1], False],
        #
        [ne, string, False],
        [ne, string[:-1], True],
        #
        [gt, string, False],
        [gt, string[:-1], True],
        [gt, string + string, False],
        [gt, add_to_last_char(string, 1), False],
        [gt, add_to_last_char(string, -1), True],
        #
        [lt, string, False],
        [lt, string[:-1], False],
        [lt, string + string, True],
        [lt, add_to_last_char(string, 1), True],
        [lt, add_to_last_char(string, -1), False],
        #
        [ge, string, True],
        [ge, string[:-1], True],
        [ge, string + string, False],
        [ge, add_to_last_char(string, 1), False],
        [ge, add_to_last_char(string, -1), True],
        #
        [le, string, True],
        [le, string[:-1], False],
        [le, string + string, True],
        [le, add_to_last_char(string, 1), True],
        [le, add_to_last_char(string, -1), False],
    ]
    obj = Model(string=string)

    for operator, b_operand, expected in operator_result_list:
        assert operator(obj.string, b_operand) is expected


# TODO: comparsions for datetime
