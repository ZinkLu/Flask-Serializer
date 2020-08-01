# -*- coding: utf-8 -*-
from collections import defaultdict

from sqlalchemy import true
from sqlalchemy.sql.operators import like_op, ilike_op

from flask_serializer.utils.empty import Empty
from . import FieldFunctionBase

PROCESSOR = defaultdict(lambda: lambda x: x)


def _like_right_side(value):
    return value + "%"


def _like_full_side(value):
    return "%" + value + "%"


PROCESSOR[like_op] = _like_right_side
PROCESSOR[ilike_op] = _like_right_side


class Filter(FieldFunctionBase):
    """当一个字段被传入, 应该使用Filter来制造一个传入Query.filter的对象"""

    def __init__(self, operator, field=None, value_process=True, default=Empty, **extra):
        """:type operator callable"""
        self.column = field
        self.operator = operator
        self.extra = extra
        self.value_process = value_process
        self.default = default  # 虽然field.Field中也有default, 但是那边是序列化时使用的, 这边是过滤条件的默认值, 不会改变data中的内容

    def to_filter(self, value=Empty):
        """
        :param value: 需要查询的值, 如果没有设置值则使用default, 如果default没有设置则使用true来代替?
        """
        field = self.column

        # 如果没有传值但是设置了默认值, 使用默认值代替value, 否则使用true来作为占位符
        if value is Empty:
            if self.default is not Empty:
                value = self.default
            else:
                return true()

        if self.value_process:

            if callable(self.value_process):
                value = self.value_process(value)

            value = self._value_process(value)

        return self.operator(field, value)

    def _value_process(self, value):
        return PROCESSOR[self.operator](value)
