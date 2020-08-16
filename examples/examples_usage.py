import datetime
import sys
sys.path.append("/Users/zinklu2/Projects/Flask-Serializer")

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_serializer import FlaskSerializer
from sqlalchemy import Column, ForeignKey, BOOLEAN, INTEGER, VARCHAR, DATE, DECIMAL
from sqlalchemy.orm import relationship
from marshmallow import Schema, fields
from flask_serializer.mixins.details import DetailMixIn
from marshmallow import fields
from flask_serializer.mixins.lists import ListModelMixin
from flask_serializer.func_field.filter import Filter
from sqlalchemy.sql.operators import eq as eq_op, like_op


now = datetime.datetime.now

app = Flask(__name__)

# SQL: CREATE DATABASE test;
# YOUR NAME REPALCE HERE
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://zinklu2@localhost:5432/test'
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)
session = db.session

fs = FlaskSerializer(app, strict=False)


# ##############  MODEL DECLARATION ###############
class Status:
    VALID = True
    INVALID = False


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(INTEGER, primary_key=True, autoincrement=True,
                nullable=False, comment=u"主键")
    is_active = Column(BOOLEAN, nullable=False, default=Status.VALID)
    create_date = Column(DATE, nullable=False, default=now)
    update_date = Column(DATE, nullable=False, default=now, onupdate=now)

    def delete(self):
        self.is_active = Status.INVALID
        return self.id

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.id}>"


class Order(BaseModel):
    __tablename__ = "order"
    order_no = Column(VARCHAR(32), nullable=False, default=now, index=True)

    order_lines = relationship("OrderLine", back_populates="order")


class OrderLine(BaseModel):
    __tablename__ = "order_line"
    order_id = Column(ForeignKey(
        "order.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(ForeignKey(
        "product.id", ondelete="RESTRICT"), nullable=False)

    price = Column(DECIMAL(scale=2))
    quantities = Column(DECIMAL(scale=2))

    order = relationship("Order", back_populates="order_lines")

    @property
    def total_price(self):
        return self.price * self.quantities


class Product(BaseModel):
    __tablename__ = "product"

    product_name = Column(VARCHAR(255), index=True, nullable=False)
    sku_name = Column(VARCHAR(64), index=True, nullable=False)
    standard_price = Column(DECIMAL(scale=2), default=0.0)
# ###############


db.create_all()


#################   SCHEMA EXAPMLE  #################


class BaseSchema(fs.Schema):
    id = fields.Integer()
    create_date = fields.DateTime(dump_only=True)
    update_date = fields.DateTime(dump_only=True)
    is_active = fields.Boolean(dump_only=True)


#################   DetaliMixIn EXAPMLE  #################


class ProductSchema(DetailMixIn, BaseSchema):
    __model__ = Product

    product_name = fields.String(required=True)
    sku_name = fields.String(required=True)
    standard_price = fields.Float()


raw_data = {
    "product_name": "A-GREAT-PRODUCT",
    "sku_name": "GP19930916",
    "standard_price": 100,
}

ps = ProductSchema()
product_instance = ps.load(raw_data)
session.commit()
print(product_instance)

raw_data = {
    "id": 1,
    "standard_price": 100,
}
ps = ProductSchema(partial=True)
product_instance = ps.load(raw_data)
session.commit()
print(product_instance)


#################   ListModelMixIN EXAPMLE #################

# basic usage
class ProductListSchema(ListModelMixin, BaseSchema):
    __model__ = "Product"

    product_name = fields.String(filter=Filter(eq_op))


raw_data = {
    "product_name": "A-GREAT-PRODUCT",
    "limit": 10,
    "offset": 0
}

pls = ProductListSchema()

product_list = pls.load(raw_data)
print(product_list)


# field
class ProductListSchema(ListModelMixin, BaseSchema):
    __model__ = Product

    name = fields.String(data_key="product_name",
                         filter=Filter(eq_op, "product_name"))


raw_data = {
    "product_name": "A-GREAT-PRODUCT",
    "limit": 10,
    "offset": 0
}

pls = ProductListSchema()

product_list = pls.load(raw_data)
print(product_list)


# value_process
class ProductListSchema(ListModelMixin, BaseSchema):
    __model__ = "Product"

    product_name = fields.String(filter=Filter(
        like_op, value_process=lambda x: f'%{x}%'))


raw_data = {
    "product_name": "PRODUCT",
    "limit": 10,
    "offset": 0
}

pls = ProductListSchema()

product_list = pls.load(raw_data)
print(product_list)


# default

for product in product_list:
    product.delete()

session.flush()
session.commit()


class ProductListSchema(ListModelMixin, BaseSchema):
    __model__ = Product

    is_active = fields.Boolean(filter=Filter(eq_op, default=True))

    product_name = fields.String(filter=Filter(eq_op))


raw_data = {
    "product_name": "A-GREAT-PRODUCT",
    "limit": 10,
    "offset": 0
}

pls = ProductListSchema()

print(pls.load(raw_data))

from flask_serializer.func_field.query import Query
from flask_serializer.mixins.lists import ListMixin

class ProductListSchema(ListMixin, BaseSchema):
    __model__ = Product

    product_name = fields.String(filter=Filter(eq_op), query=Query(label="name"))

raw_data = {
    "page": 1,
    "size": 10,
    "product_name": "A-GREAT-PRODUCT",
}

pls = ProductListSchema()

product_list = pls.load(raw_data)
product = product_list[0]
print(product.product_name)
print(product.name)
print(product[0])