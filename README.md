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

示例代码可以看[这里]("examples/examples.py")

如果你已经十分熟悉了marshmallow的使用, 你可以直接跳过3.3

### 3.1 初始化

如同其他的flask插件, flask-serializer的初始化也很简单; 

> 注意: 由于依赖flask-SQLAlchemy, flask-serializer应该在其之后进行初始化

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_serializer import FlaskSerializer

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres@localhost:5432/test'

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

        def __repr__(self):
            return f"<{self.__class__.__name__}:{self.id}>"
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
    session.flush()
    session.commit()
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

序列化可以直接使用marshmallow方法, 这里我们主要介绍反序列化方法

### 3.4 使用DetailMixin进行反序列化

上面我们看到, 第二种方法还是比较Nice的(官网文档中也有事例), 他直接使用了marshmallow post_load方法, 对结果进行后处理, 得到一个Product对象, 实际上DetailMix就是实现了这样方法的一个拓展类.

1. 使用DetailMixin进行模型创建:
   
    很简单, 导入DetailMixIN后使得刚才的ProductSchema继承DetailMixIN, 然后为添加`__model__`到类中, 设置这个Schema需要绑定的对象.
   
    ```python
    from marshmallow import Schema, fields

    from flask_serializer.mixins.details import DetailMixin 

    class BaseSchema(fs.Schema):
        id = fields.Integer()
        create_date = fields.DateTime(dump_only=True)
        update_date = fields.DateTime(dump_only=True)
        is_active = fields.Boolean(dump_only=True)
    
    class ProductSchema(DetailMixin, BaseSchema):
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
    ```

    ```sh
    <Product:1>
    ```

    > 注意: DetailMixin 会调用flush()方法, 除非session开启了autocommit, 否则不会提交你的事务(autocommit也是新创建了一个子事务, 不会提交当前主事务), 请开启flask_sqlalchemy的自动提交事务功能或者手动提交

> `__model__`说明: 如果有导入问题, `__model__`支持设置字符串并在稍后的代码中自动读取SQLAlchemy的metadata并且自动设置对应的Model类
>
>    ```python
>    class ProductSchema(DetailMixin, Schema):
>        __model__ = "Product"
>    ```

2. 使用DetailMixin进行模型更新

    既然有创建就有更新, DetailMixin能够自动读取`__model__`里面的主键(前提是model主键必须唯一), 当在读取到原始数据中的主键时, load方法会自动更新而不是创建这个模型. 当然, 也不要忘记在schema中定义你的主键字段.

    ```python
    raw_data = {
        "id": 1,
        "standard_price": 10000000,
    }

    ps = ProductSchema(partial=True)  # partial参数可以使得required的字段不进行验证, 适合更新操作

    product_instance = ps.load(raw_data)
    session.commit()
    ```

    ```sh
    <Product:1>
    ```

    > 如果只是想读取这个模型, 而不想更新, 只需要传入主键值行就行
    > 
    > TODO: 以后可以加入`ReadOnlyDetailMixIN`

还有一些其他的特性, 我们在进阶中再看, 配合上SQLAlchemy的relationship, 还可以实现更多.

### 3.5 使用ListMixin进行查询

DetailMixin支持的是增改操作(实际上也支持删除, 但未来需要添加专门用来删除的Mixin), 而ListMixin支持查询的操作.

下面是不同的ListMixin的使用

#### 3.5.1 ListModelMixin

ListModelMixin 顾名思义是针对某个模型的查询, 其反序列化的结果自然是模型实例的列表

为了让用户的输入能够转化成我们想要的查询, 这里使用`Filter`对象作为参数`filter`传入`Field`的初始化中

1. 基本使用

    ```python
    from flask_serializer.mixins.lists import ListModelMixin
    from sqlalchemy.sql.operators import eq as eq_op

    class ProductListSchema(ListModelMixin, BaseSchema):
        __model__ = Product

        product_name = fields.String(filter=Filter(eq_op))
    ```

    此时, 我们接口接收到输入的参数, 我们这样: 

    ```python
    raw_data = {
        "product_name": "A-GREAT-PRODUCT",
    }

    pls = ProductListSchema()

    product_list = pls.load(raw_data)
    ```

    ```sh
    Traceback (most recent call last):
    ....
    marshmallow.exceptions.ValidationError: {'_schema': ['分页信息错误, 必须提供limit/offset或者page/size']}
    ```

    阿偶, 报错了, 实际上, ListModelMixin中会去自动检查Limit/Offset或者Page/Size这样的参数, 如果你不想让数据库爆炸, 可别忘记传入这两个参数!

    ```python
    raw_data["page"] = 1
    raw_data["size"] = 10
    product_list = pls.load(raw_data)
    ```

    ```sh
    [<Product:1>]
    ```

2. 排序\*
   
    如果想使用排序, 可以重写这一个方法
    
    ```python
    class ProductListSchema(ListModelMixin, BaseSchema):
        __model__ = Product

        product_name = fields.String(filter=Filter(eq_op))

        def order_by(self, data):
            return self.model.update_date.desc()
    ```

    注意了, `self.model`可以安全的取到设置的`__model__`指代的对象, 无论它被设置成字符串还是Model类.

    > \* 这方方法可能需要重新设计一下, 我们可以将其变成一个属性而不是提供一个可重写的方法, 除非排序非常复杂

#### 3.5.2 Filter类参数说明

 1. `operator`, 这代表着将要对某一个字段做什么样的操作, 这个参数应该是`sqlalchemy.sql.operators`下提供的函数, Filter会自动套用这些函数, 将转化成对应的WHERE语句, 上面的例子中, 我们最终得到的SQL就是这样的

     ```sql
     SELECT * FROM product WHERE product_name = 'A-GREAT-PRODUCT' ORDER BY product.update_date DESC
     ```

 2. `field`, 如果不设置, 他将默认使用`__model__`下面的同名Column进行过滤, 所以, 当你的Schema和Model的Filed对不上时, 也可以这样搞

     ```python
     class ProductListSchema(ListModelMixin, BaseSchema):
         __model__ = Product

         name = fields.String(filter=Filter(eq_op, Product.product_name))
     ```

     这时, 我们的接口文档中还定义的是`product_name`, Schema将读不到该值, 所以, 接口文档, shecma, model中定义的字段名字可能都不一样, 但是他们指代的同一个东西是, 你还可以这么做: 

     ```python
     class ProductListSchema(ListModelMixin, BaseSchema):
         __model__ = Product

         name = fields.String(data_key="product_name", filter=Filter(eq_op, Product.product_name))
     ```

     `data_key`是marshmallow自带的参数, 他将告诉Field对象从哪里取值.

     > 在Marshmallow2中, 这个参数叫`load_from`和`dump_from`, 现在合并了, 但实际上好像适用范围变小了.

     同样的, `field`也可以被设置为字符串, 且可以省略model的名称

     ```python
     class ProductListSchema(ListModelMixin, BaseSchema):
         __model__ = Product

         name = fields.String(data_key="product_name", filter=Filter(eq_op, "product_name"))
    ```

    对于`field`参数, 还可以设置为其他模型的Column, 我们放到进阶部分去讲吧

3. `value_process`对即将进行查询的值进行处理, 一般情况下用在诸如`like`的操作上

    `value_procee`支持传入一个`callable`对象, 并且只接受一个参数, 返回值该参数的处理.
   
    ```python
    from sqlalchemy.sql.operator import like_op

    class ProductListSchema(ListModelMixin, BaseSchema):
        __model__ = Product

        product_name = fields.String(filter=Filter(eq_op, value_process=lambda x: f"%{x}%"))
    
    raw_data = {
        "product_name": "PRODUCT",
        "limit": 10,
        "offset": 0
    }

    pls = ProductListSchema()

    product_list = pls.load(raw_data)
    print(product_list)
    ```

    ```sql
    SELECT * FROM product WHERE product_name LIKE '%PRODUCT%'
    ```

    ```sh
    [<Product:1>]
    ```

    > 事实上, `value_process`也有默认值, 如果你使用`like_op`或者`ilike_op`则会自动在value后面加上`%`(右模糊匹配)

    > 其实`pre_load`装饰器也可以预处理值, 但是我认为不需要写太多了预处理方法

4. `default`默认值.

    有时可能会有不传值使用默认值进行过滤的情况, 可以设置`default`方法.

    > 这个场景下不能设置marshmallow的Field对象的default参数, 因为这个default是给dump方法用的, 而不是load方法.

    让我们先来删除刚才创建的product

    ```python
    # delete a product
    for product in product_list:
        product.delete()
    
    session.flush()
    session.commit()
    ```

    然后我们创建这样一个Schema, 将自动过滤掉软删除的记录
    
    ```python
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
    ```

    ```sh
    []
    ```

#### 3.5.3 ListMixin

和ListModelMixin的差别就是这个方法这对一个`Model`进行全部查询, 而是会对指定的一些字段进行查询, 这样可以避免一些额外的性能开销, 只查询你感兴趣的字段. 并且可以完成跨模型的字段查询.

ListMixin需要一个`Query`对象来告诉他需要查询的字段

1. 基本使用:

    ```python
    from flask_serializer.func_field.filter import Filter
    from flask_serializer.func_filed.query import Query
    from flask_serializer.mixins.lists import ListMixin
    from sqlalchemy.sql.operators import eq as eq_op

    class ProductListSchema(ListMixin, BaseSchema):
        __model__ = Product

        product_name = fields.String(filter=Filter(eq_op), query=Query())
    ```

    同样的, 让我们输入参数

    ```python
    raw_data = {
        "page": 1,
        "size": 10,
        "product_name": "A-GREAT-PRODUCT",
    }

    pls = ProductListSchema()

    product_list = pls.load(raw_data)
    ```

    这是时候我们得到的不再是`Product`的实例列表, 而是`sqlalchemy.util._collections.result`对象, 这种数据结构有一点像具名元组, 可以进行下标索引和`.`操作, 但是他只包含你查询的字段, 不包含任何其他多余的字段, 因此:

    ```python
    product = product_list[0]  # 如果没有的话记得新建一条记录哦!

    print(product.product_name)
    print(product[0])
    ```

    ```sh
    A-GREAT-PRODUCT
    A-GREAT-PRODUCT
    ```

#### 3.5.4 Query的参数说明

1. `field`
   
    可以是一个SQLAlchemy的Column对象, 也可以是能够被正确指向Column的字符串. 这个参数将会告诉Query查询的字段到底是什么, 如果不填写则直接使用当前`field`的名称对应`__model__`字段进行查询.

    其实`field`完全可以设置另外一个模型的字段, 如果这两个模型之间有外键的关联, SQLAlchemy会自动为我们拼接上Join语句, 并且加上正确的On条件, 如果这两个模型没有直接外键的关联, 也可以重写`def modify_before_query(self, query, data)`方法来增加自己的Join条件, 我们放到高级部分去讲解.

2. `label`

    label参数相当于SQL语句中的`AS`

    ```python
    class ProductListSchema(ListMixin, BaseSchema):
        __model__ = Product

        product_name = fields.String(filter=Filter(eq_op), query=Query(label="name"))
    
    pls = ProductListSchema()

    product = pls.load(raw_data)[0]

    print(product.name)

    product.product_name # raise a AttributeError
    ```

    ```sh
    A-GREAT-PRODUCT

    Traceback (most recent call last):
    File xxxxxx
        print(product.product_name)
    AttributeError: 'result' object has no attribute 'product_name'
    ```

## 4 进阶

### 3.6.1 结合Nest和relationship完成骚操作

### 3.6.2 外键检查

### 3.6.3 联合过滤

## 已知问题

1. DetailMixin不能兼容sqlite, sqlite不支持批量更新

## TODO

1. 可以读取Model中的Column, 根据Column自动生成Field.

2. JsonSchema自动转换成Marshallmallow-Schema.

3. DeleteMixIN, 支持批量删除的Serializer.

4. ...