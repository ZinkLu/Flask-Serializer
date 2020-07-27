from marshmallow import post_load

from flask_serializer.cache_object.cached import CachedModel


class _MixinBase(object):
    # __model__ = None  # type Base

    _model = None

    model = CachedModel()

    @post_load
    def make_queries(self, data, **kwargs):
        """
        实现 make_queries 方法, 将data中的数据反序列化成Instance
        :param data: data
        """
        return NotImplemented
