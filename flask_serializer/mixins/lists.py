from functools import reduce

from marshmallow import fields
from marshmallow import pre_load, post_load, validates_schema
from marshmallow.exceptions import ValidationError
from sqlalchemy import and_, func, true

from flask_serializer.mixins import _MixinBase
from flask_serializer.utils.empty import Empty


class PreLoadListMixin:
    """
    该MixIn可以将查询字符串中以逗号分隔的字符串转变为列表, 如:
    ?cate=1,2,3 查询分类id为1,2,3下面的spu
    sql 为 cate IN (1,2,3)
    """

    @pre_load
    def split_into_list(self, data, *args, **kwargs):
        """
        自动转化所有Str to ListField
        :param data
        :return:
        """
        data = data.copy()
        fs = self.fields
        list_fields = [k for k, v in fs.items() if isinstance(v, fields.List)]
        for l in list_fields:
            if data.get(l):
                data[l] = data[l].split(",")
        return data


class ListBase(_MixinBase):
    """将Filter字段转换为Filter, 将各种条件拼接成SQL"""

    def fields_to_filters(self, fields_info):
        """
        重写这个方法来自定义过滤条件, 正常情况下, 使用AND对条件进行连接
        """
        filter_list = list()

        for filter_field, field_value in fields_info.items():
            # field_value 可能是Empty
            filter_list.append(filter_field.to_filter(field_value))

        return reduce(and_, filter_list) if filter_list else true()

    def order_by(self, data):
        return true()

    def modify_before_query(self, query, data):
        """增加query的一些东西, 比如JOIN条件等"""
        return query

    def modify_after_query(self, query, data):
        """增加一些query东西, 比如limit offset等"""
        return query

    def to_sql(self, data):
        """
        :param data  验证的数据
        将query套用在Model上, 重写这个方法来修改sql
        """
        query = self.get_query(data)
        query = self.modify_before_query(query, data)
        filters = self.get_filters(data)
        order_by = self.order_by(data)
        return self.modify_after_query(query.filter(filters).order_by(order_by), data)

    def get_query(self, data):
        """获得需要查询的东西, 一般来说是一个模型, 也可以是联合查询, 重写这个方法来获得想要的query, 例如一些join"""
        return self.db.session.query(self.model)

    def get_filters(self, data):
        real_query_field = {field_info: data.get(
            field_info.field_name, Empty) for field_info in self.filter_fields}

        filters = self.fields_to_filters(real_query_field)
        return filters

    @post_load
    def make_queries(self, data, **kwargs):
        return self.to_sql(data).all()


class ListModelMixin(ListBase):
    """
    增加了分页, 检查分页, mixin应该放在ma.ModelSchema之前
    """

    limit = fields.Integer(load_only=True)
    offset = fields.Integer(load_only=True)
    page = fields.Integer(load_only=True)
    size = fields.Integer(load_only=True)

    @validates_schema
    def validate_for_pagination(self, data, **kwargs):
        """验证limit和offset或者page/size"""
        limit = data.get("limit")
        offset = data.get("offset")
        page = data.get("page")
        size = data.get("size")

        if not any((limit is None, offset is None)):
            # limit/offset必须一起传入
            if any((limit < 1, offset < 0)):
                raise ValidationError("limit/offset必须大于0")
            return

        if not any((page is None, size is None)):
            # page/size必须一起传入
            if any((page < 1, size < 1)):
                raise ValidationError("page/size必须大于0")
            return

        raise ValidationError("分页信息错误, 必须提供limit/offset或者page/size")

    @post_load
    def convert_page_to_limit(self, data, *args, **kwargs):
        """将page转换成limit"""
        if data.get("page"):
            limit = data["size"]
            offset = data["size"] * (data["page"] - 1)
            data["limit"] = limit
            data["offset"] = offset
        return data

    def modify_after_query(self, query, data):
        return query.limit(data["limit"]).offset(data["offset"])


class ListMixin(ListModelMixin):
    """不直接查询模型, 而是以select的方式查询, 提供一些方法, 来命中覆盖索引"""

    def _get_query(self, data):
        return tuple(query_field.to_query() for query_field in self.query_fields)

    def get_query(self, data):
        if not self.query_fields:
            return self.db.session.query(*self.model.__table__.columns.values())

        return self.db.session.query(*self._get_query(data))


class CountMixin(ListBase):

    def get_query(self, data):
        return self.db.session.query(func.count()).select_from(self.model)

    @post_load
    def make_queries(self, data, **kwargs):
        return self.to_sql(data).first()[0]
