"""Unit tests in addition to doctests present."""
from datetime import datetime, timedelta
from operator import add, eq, floordiv, ge, gt, le, lt, mod, mul, ne, pow, sub, truediv
from random import randint
from typing import Optional

from rss_parser.models import XMLBaseModel
from rss_parser.models.types.tag import Tag


class Model(XMLBaseModel):
    number: Optional[Tag[int]]
    float_number: Optional[Tag[float]]
    string: Optional[Tag[str]]
    datetime: Optional[Tag[datetime]]


def rand_str():
    # FIXME: Yeah I know
    return "string"


def rand_dt():
    return datetime(randint(1, 2023), randint(1, 12), randint(1, 28))


def rand_td():
    return timedelta(randint(1, 1000))


def test_comparison_operators_number():
    number = randint(0, 2**32)
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
    number = float(randint(0, 2**32))
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


def test_comparison_operators_datetime():
    dt = rand_dt()
    delta = rand_td()
    operator_result_list = [
        [eq, dt, True],
        [eq, dt + delta, False],
        [eq, dt - delta, False],
        #
        [ne, dt, False],
        [ne, dt + delta, True],
        [ne, dt - delta, True],
        #
        [gt, dt, False],
        [gt, dt + delta, False],
        [gt, dt - delta, True],
        #
        [lt, dt, False],
        [lt, dt + delta, True],
        [lt, dt - delta, False],
        #
        [ge, dt, True],
        [ge, dt + delta, False],
        [ge, dt - delta, True],
        #
        [le, dt, True],
        [le, dt + delta, True],
        [le, dt - delta, False],
    ]
    obj = Model(datetime=dt)

    for operator, b_operand, expected in operator_result_list:
        assert operator(obj.datetime, b_operand) is expected


def test_arithmetic_operators_number():
    number = randint(0, 2**32)
    b_operand = randint(0, 2**16)
    operator_list = [add, sub, mul, truediv, floordiv, mod, pow]
    obj = Model(number=number)

    for operator in operator_list:
        assert operator(obj.number, b_operand) == operator(number, b_operand)


def test_arithmetic_operators_float():
    number = randint(0, 2**8) / 100
    b_operand = randint(0, 2**8) / 100
    operator_list = [add, sub, mul, truediv, floordiv, mod, pow]
    obj = Model(floatNumber=number)

    for operator in operator_list:
        assert operator(obj.float_number, b_operand) == operator(number, b_operand)


def test_arithmetic_operators_string_mul():
    string = rand_str()
    int_operand = randint(0, 2**16)
    string_operand = rand_str()
    obj = Model(string=string)

    assert mul(obj.string, int_operand) == mul(string, int_operand)
    assert add(obj.string, string_operand) == add(string, string_operand)


def test_arithmetic_operators_datetime():
    dt = rand_dt()
    td_operand = rand_td()
    operator_list = [add, sub]
    obj = Model(datetime=dt)

    for operator in operator_list:
        assert operator(obj.datetime, td_operand) == operator(dt, td_operand)
