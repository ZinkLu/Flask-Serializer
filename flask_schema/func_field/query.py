# -*- coding: utf-8 -*-
from six import string_types

from . import FieldFunctionBase


class Query(FieldFunctionBase):

    def __init__(self, field=None, label=None):
        self.column = field
        self.label = label

    def to_query(self):
        if self.column is None:
            self.column = getattr(self.model, self.field_name)
        elif isinstance(self.column, string_types):
            self.column = getattr(self.model, self.column)
        return self.column.label(self.label) if self.label else self.column
