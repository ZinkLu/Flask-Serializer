# Flask-Serializer

一个帮助你快速书写Restful的序列化器工具

## 1. 简介

后端程序员, 最基础也是最常做的事情就是定义数据库模型并进行增删改查, 而在一个Restful接口集合中, 对资源进行增删改查的也离不开参数的校验.

从Json校验到持久化成数据库记录, 这个过程被我们成为反序列化(狭义), 而从数据库表到Json字符串, 这个过程我们成为序列化(狭义).

本软件就是这样一个序列化工具, 它旨在让反序列化和反序列化更加快捷和方便, 让我们更关注业务逻辑(而不是参数校验和增删改查).

## 2. 安装说明

需求: 

flask-serializer 支持Python >= 2.7的版本.

> python2.7: 使用Marshmallow2
>
> python 3: 使用Marshmallow3

安装:

```sh
pip install flask-serializer
```

## 3. 使用

如果你已经十分熟悉了marshmallow的使用, 你可以直接跳过3.3

### 3.1 初始化

如同其他的flask插件, flask-serializer的初始化也很简单; 

> 注意: 由于依赖flask-SQLAlchemy, flask-serializer应该在其之后进行

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_serializer import FlaskSerializer

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:postgres@localhost:5432/test'

db = SQLAlchemy(app)
session = db.session

fs = FlaskSerializer(app, strict=False)
```

keyword arguments 将会转换为Marshmallow的`class Meta`, 详细看[这里](https://marshmallow.readthedocs.io/en/stable/quickstart.html#handling-unknown-fields)

然后, 这样定义一个schema:

```python
class BaseSchema(fs.Schema):
    pass
```

### 3.2. 准备

我们设计一系列模型: 

1. 模型基类, 提供所有模型的通用字段

    ```python
    db = SQLAlchemy(app)

    now = datetime.datetime.now

    class Status:
        VALID = True
        INVALID = False

    class BaseModel(db.Model):
        __abstract__ = True

        id = Column(INTEGER, primary_key=True, autoincrement=True, nullable=False, comment=u"主键")
        is_active = Column(BOOLEAN, nullable=False, default=Status.VALID)
        create_date = Column(DATE, nullable=False, default=now)
        update_date = Column(DATE, nullable=False, default=now, onupdate=now)

        def delete(self):
            self.is_active = Status.INVALID
            return self.id
    ```

2. 订单模型

    ```python
    class Order(BaseModel):
        __tablename__ = "order"
        order_no = Column(VARCHAR(32), nullable=False, default=now, index=True)

        order_lines = relationship("OrderLine", back_populates="order")
    ```

3. 订单明细行, 与订单模型是多对一的关系, 记录了该订单包含的商品数量价格等信息

    ```python
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
    ```

4. 商品模型, 与订单明细行是一对多的关系, 记录了商品的基本属性

    ```python
    class Product(BaseModel):
        __tablename__ = "product"

        product_name = Column(VARCHAR(255), index=True, nullable=False)
        sku_name = Column(VARCHAR(64), index=True, nullable=False)
        standard_price = Column(DECIMAL(scale=2), default=0.0)
    ```

### 3.3. 简单的Marshmallow演示

更加高级的使用技巧, 请看: [Marshmallow文档](https://marshmallow.readthedocs.io/en/stable/)

#### 3.2.1. 反序列化

1. 假设我们现在要创建一条数据库记录, 创建一个schema来验证数据

    ```python
    from marshmallow import Schema, fields

    class ProductSchema(Schema):
        product_name = fields.String(required=True)
        sku_name = fields.String(required=True)
        standard_price = fields.Float()
    ```

    我们可以这样做

    ```python
    raw_data = {
        "product_name": "A-GREAT-PRODUCT",
        "sku_name": "GP19930916",
        "standard_price": 100 ,
    }

    ps = ProductSchema()

    instance_data = ps.validate(raw_data)  # marshmallow2 will return (data, error) tuple

    product = Product(**instance_data)

    session.add(product)
    session.commit()
    session.flush()
    ```

2. 或者使用marshmallow自带的post_load方法

    ```python
    from marshmallow import Schema, fields, post_load

    class ProductSchema(Schema):
        product_name = fields.String(required=True)
        sku_name = fields.String(required=True)
        standard_price = fields.Float()

        @post_load
        def make_instance(data, *args, **kwargs):
            # data是通过验证的数据
            product = Product(**data)
            session.add(product)
            session.commit()
            session.flush()
            return product
    ```

    然后

    ```python
    raw_data = {
        "product_name": "A-GREAT-PRODUCT",
        "sku_name": "GP19930916",
        "standard_price": 100 ,
    }

    ps = ProductSchema()

    product_instance = ps.load(raw_data)
    ```

#### 3.1.2. 序列化

至于序列化, 也可以使用ProductSchema实例进行处理, 如:

1. 序列化, 只会取非load_only的字段进行序列化

    ```python
    product_instance = session.query(Product).get(1)
    data = ps.dump(product_instance)  # dumps will return json string; marshmallow2 will return (data, error) tuple
    ```

2. 也可以定义一些dump_only的filed用于序列化

    ```python
    class ProductSchemaAddDumpOnly(ProductSchema):
        id = fields.Integer(dump_only=True)
        create_date = fields.DateTime(dump_only=True)
        update_date = fields.DateTime(dump_only=True)
        is_active = fields.Boolean(dump_only=True)
    
    ps_with_meta = ProductSchemaAddDumpOnly()
    data = ps_with_meta.dump(product_instance)
    ```

### 3.4 使用DetailMixIn进行反序列化

上面我们看到, 第二种方法还是比较Nice的(官网文档中也有事例), 他直接使用了marshmallow post_load方法, 对结果进行后处理, 得到一个Product对象, 实际上DetailMix就是实现了这样方法的一个拓展类.

1. 使用DetailMixIn进行模型创建:
   
    很简单, 导入DetailMixIN后使得刚才的ProductSchema继承DetailMixIN, 然后为添加`__model__`到类中, 设置这个Schema需要绑定的对象.
   
    ```python
    from marshmallow import Schema, fields

    from flask_serializer.mixins.details import DetailMixIn 

    class BaseSchema(fs.Schema):
        id = fields.Integer()
        create_date = fields.DateTime(dump_only=True)
        update_date = fields.DateTime(dump_only=True)
        is_active = fields.Boolean(dump_only=True)
    
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

    data = product_instance = ps.dump(ps)
    ```

> `__model__`说明: 如果有导入问题, `__model__`支持设置字符串并在稍后的代码中自动读取SQLAlchemy的metadata并且自动设置对应的Model类
>
>    ```python
>    class ProductSchema(DetailMixIn, Schema):
>        __model__ = "Product"
>    ```

2. 使用DetailMixIn进行模型更新

    既然有创建就有更新, DetailMixIn能够自动读取`__model__`里面的主键(前提是model主键必须唯一), 当在读取到原始数据中的主键时, load方法会自动更新而不是创建这个模型. 当然, 也不要忘记在schema中定义你的主键字段.

    ```python
    raw_data = {
        "id": 1,
        "standard_price": 10000000,
    }

    ps = ProductSchema(partial=True)  # partial参数可以使得required的字段不进行验证, 适合更新操作

    product_instance = ps.load(raw_data)

    data = ps.dump(product_instance)
    ```

    > 如果只是想读取这个模型, 而不想更新, 只需要传入主键值行就行

还有一些其他的特性, 我们在进阶中再看, 配合上SQLAlchemy的relationship, 还可以实现更多.

### 3.5 使用ListMixIn进行查询

DetailMixIn支持的是增改操作(实际上也支持删除, 但未来需要添加专门用来删除的MixIn), 而ListMixIn支持查询的操作.

下面是不同的ListMixIn的使用

#### 3.5.1 ListModelMixin

#### 3.5.2 ListMixin

## 进阶

## 已知问题

1. DetailMixin不能兼容sqlite, sqlite不支持批量更新

## TODO

1. 可以读取Model中的Column, 根据Column自动生成Field.

2. JsonSchema自动转换成Marshallmallow-Schema.

3. DeleteMixIN, 支持批量删除的Serializer.