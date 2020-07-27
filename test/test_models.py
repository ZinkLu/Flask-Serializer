# -*- coding: utf-8 -*-
import datetime
from contextlib import contextmanager

from sqlalchemy import Column, ForeignKey, BOOLEAN, INTEGER, VARCHAR, DATE, DECIMAL
from sqlalchemy.orm import relationship

from test.test_app import db, session


class Status:
    VALID = True
    INVALID = False


now = datetime.datetime.now


class BaseModel(db.Model):
    __abstract__ = True
    sqlite_autoincrement = True

    id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False, comment=u"主键")
    is_active = Column(BOOLEAN, nullable=False, default=Status.VALID)
    create_date = Column(DATE, nullable=False, default=now)
    update_date = Column(DATE, nullable=False, default=now, onupdate=now)

    def delete(self):
        self.is_active = Status.INVALID
        return self.id

    @contextmanager
    def auto_commit(self):
        try:
            yield
            session.commit()
            session.flush()
        except Exception as e:
            session.rollback()
            raise e


class Order(BaseModel):
    __tablename__ = "order"
    order_no = Column(VARCHAR(32), nullable=False, default=now, index=True)

    order_lines = relationship("OrderLine", back_populates="order")


class OrderLine(BaseModel):
    __tablename__ = "order_line"
    order_id = Column(ForeignKey("order.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(ForeignKey("product.id", ondelete="RESTRICT"), nullable=False)

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


db.create_all()
