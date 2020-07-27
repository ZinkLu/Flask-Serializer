# -*- coding: utf-8 -*-
"""
测试__model__和func_field传入Python对象时是否有用

"""

from marshmallow import fields
from sqlalchemy.sql.operators import eq

from flask_serializer.func_field.filter import Filter
from flask_serializer.func_field.foreign import Foreign
from flask_serializer.mixins.details import DetailMixIn
from test.test_app import fs, session
from test.test_models import Status, OrderLine, Product, Order


class BaseSchema(fs.Schema):
    id = fields.Integer()
    create_date = fields.DateTime()
    update_date = fields.DateTime()
    is_active = fields.Boolean(filter=Filter(eq, default=Status.VALID))


class OrderLineSchema(DetailMixIn, BaseSchema):
    __model__ = OrderLine
    product_id = fields.Integer(foreign=Foreign(OrderLine.product_id))

    price = fields.Float(required=True)
    quantities = fields.Float(required=True)

    total_price = fields.Float(dump_only=True)

    order = fields.Nested(lambda: OrderSchema, load_only=True)


class OrderSchema(DetailMixIn, BaseSchema):
    __model__ = Order
    order_no = fields.String(dump_only=True)

    order_lines = fields.List(fields.Nested(lambda: OrderLineSchema))
    order_line_ids = fields.List(fields.Integer(), foreign=Foreign(OrderLine.order_id))


class ProductSchema(DetailMixIn, BaseSchema):
    __model__ = Product
    product_name = fields.String(required=True)
    sku_name = fields.String(required=True)
    standard_price = fields.Float()


ps = ProductSchema()
os = OrderSchema()
ols = OrderLineSchema()

PRODUCT_ID = 1
ORDER_ID = 1


def test_create_product():
    product = dict(product_name='星爸爸马克杯', sku_name='0000001', standard_price="100", )
    product_instance = ps.load(product)
    with product_instance.auto_commit():
        session.add(product_instance)


def test_create_order():
    order = dict(order_lines=[dict(product_id=1, price=100, quantities=1)])
    order_instance = os.load(order, partial=True)
    with order_instance.auto_commit():
        session.add(order_instance)


def test_update_order():
    # ORDER_ID = 1
    order = dict(id=1, order_lines=[dict(product_id=1, price=10, quantities=2)])
    order_instance = os.load(order, partial=True)
    with order_instance.auto_commit():
        session.add(order_instance)
    print(os.dump(order_instance))


def test_update_order_with_order_ids():
    order = dict(id=1, order_line_ids=[1])
    order_instance = os.load(order, partial=True)
    with order_instance.auto_commit():
        session.add(order_instance)
    print(os.dump(order_instance))


def test_create_order_lines_while_create_order():
    order_lines = dict(product_id=1, price=10, quantities=2, order=dict())
    order_lines_instance = ols.load(order_lines, partial=True)
    with order_lines_instance.auto_commit():
        session.add(order_lines_instance)
    print(ols.dump(order_lines_instance))


def test_update_order_lines_while_create_order():
    order_lines = dict(product_id=1, price=10, quantities=2, id=1, order=dict())
    order_lines_instance = ols.load(order_lines, partial=True)
    with order_lines_instance.auto_commit():
        session.add(order_lines_instance)
    print(ols.dump(order_lines_instance))
