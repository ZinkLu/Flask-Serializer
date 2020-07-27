# -*- coding: utf-8 -*-

from collections import OrderedDict

from flask import Flask
from marshmallow.schema import SchemaMeta, BaseSchema as _BaseSchema
from six import string_types

from flask_serializer.mixins import _MixinBase


# 重写metaclass, 处理一些fields


class NewSchemaMeta(SchemaMeta):

    def _init_function_field(self):
        if not getattr(self, "__model__", None):
            return (), (), ()

        filter_fields = getattr(self, "filter_fields", tuple())
        query_fields = getattr(self, "query_fields", tuple())
        foreign_fields = getattr(self, "foreign_fields", tuple())

        func_fields = OrderedDict(
            filter=filter_fields, query=query_fields, foreign=foreign_fields)

        for field_name, field_obj in self._declared_fields.items():
            for func_name in ("filter", "query", "foreign"):
                field = self.init_filed_function_instance(func_name, field_name, field_obj, self.db, self.__model__)
                if field:
                    func_fields[func_name] += (field,)

        return func_fields.values()

    @classmethod
    def init_filed_function_instance(cls, func_name, field_name, field_obj, db, model):
        """初始化功能性field的实例"""
        func_instance = field_obj.metadata.get(func_name)
        if func_instance is None:
            return
        func_instance.full_init_self(db, field_name, model)
        return func_instance

    def __init__(self, name, bases, attrs):
        super(NewSchemaMeta, self).__init__(name, bases, attrs)

        if not getattr(self, "__model__", None) and not issubclass(self, _MixinBase):
            return

        model = self.__model__
        self.filter_fields, self.query_fields, self.foreign_fields = self._init_function_field()

        # DO NOT OVERRIDE property description, there is NO instance yet
        # self.model = model
        if isinstance(model, string_types):
            self._model_str = model
        else:
            self._model = model


class BaseSchema(_BaseSchema):
    pass


def make_meta(meta):
    """
    :param meta dict
    :return:
    """
    return type("Meta", (), meta)


def schema_maker(db, meta):
    """
    create a Schema class with db bind
    :param db:
    :param meta: dict key value in class Meta
    :return:
    """
    # meta["db"] = db
    meta = make_meta(meta)
    return NewSchemaMeta("BaseSchema", (BaseSchema,), dict(Meta=meta, db=db))


class FlaskSerializer(object):
    def __init__(self, app=None, db=None, **schema_meta):
        """
        :param schema_meta: meta config for marshmallow Schema
        """
        self.db = db
        self.schema_meta = schema_meta
        self.Schema = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):  # type: (Flask) -> None
        """
        :type app Flask
        初始化APP, 必须放在Flask-SQLAlchemy之后进行
        """

        db = self.db
        if db is None:
            if not app.extensions.get("sqlalchemy"):
                raise KeyError("init flask-sqlalchemy first")
            _sa = app.extensions["sqlalchemy"]
            self.db = db = _sa.db

        schema_class = schema_maker(db, self.schema_meta)
        # FieldFunctionBase.db = db
        app.extensions['flaskserializer'] = schema_class
        self.Schema = schema_class
