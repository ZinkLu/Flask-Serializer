from copy import deepcopy

from marshmallow import post_load, validates_schema
from marshmallow.exceptions import ValidationError
from sqlalchemy import inspect

from flask_serializer.mixins import _MixinBase


class DetailMixIn(_MixinBase):
    """
    提供了外键的验证, 并且在返回实例的时候会将多对一的关联给改掉
    一般用于post或者put方法, 修改模型时

    **特别说明**:
        - `key_check`则是用来检查外键是否合法, 而`fk`参数是用来创建/修改关联(更新表数据)

            - key_check: `SELECT id FROM one WHERE id = $1 `

            - fk: UPDATE `many SET fk = $1 WHERE many.id IN ($2)`
    """

    _pk_field = None

    @property
    def pk_field(self):
        """:rtype str"""
        if self._pk_field is not None:
            return self._pk_field

        model = self.model
        pk_field = inspect(model).primary_key
        if len(pk_field) != 1:
            raise ValueError("模型%s主键不唯一" % str(model))
        pk_field = pk_field[0].name

        self._pk_field = pk_field
        return self._pk_field

    @validates_schema
    def check_foreign_key(self, data, **kwargs):
        """自动判断外键是否存在"""
        for func_foreign in self.foreign_fields:
            if data.get(func_foreign.field_name):
                foreign_ids = data.get(func_foreign.field_name)
                if not func_foreign.foreign_check(foreign_ids):
                    raise ValidationError("外键{}检查失败".format(func_foreign.field_name),
                                          field_names=func_foreign.field_name)

        return data

    def make_instance(self, data):
        """创建instance, 关联relations, 如果是不需要创建或者修改可以直接返回data
        `fk`用于在这里创建关联.
        默认使用id作为主键
        """
        _data = deepcopy(data)
        if _data.get(self.pk_field):
            # update
            _id = _data.pop(self.pk_field)
            instance = self.get_instance(_id)
            for k, v in _data.items():

                if hasattr(instance, k):
                    # 这里处理relationship, 使用extend来处理, 而不是setattr, 保证正确性, 这个方法是真的丑陋啊
                    if hasattr(getattr(instance, k), "extend"):

                        if not isinstance(v, list):
                            v = [v]

                        getattr(instance, k).extend(v)
                        continue

                    setattr(instance, k, v)
        else:
            # create
            instance = self.model(**_data)

        _id = getattr(instance, self.pk_field)

        # 为了保证线程安全, 这里不能使用实例来存储数据
        for func_foreign in self.foreign_fields:
            if _data.get(func_foreign.field_name):
                foreign_ids = _data.get(func_foreign.field_name)
                if isinstance(foreign_ids, list):
                    func_foreign.update_foreign(_id, foreign_ids)
        
        self.db.session.add(instance)
        self.db.session.flush()
        return instance

    @post_load
    def make_queries(self, data, **kwargs):
        """Detail应该是创建或者更新一个instance而不是查询"""
        # self.check_foreign_key(data)
        return self.make_instance(data)

    def get_instance(self, instance_id):
        """获取一个模型, 修改这个方法添加逻辑删除规则"""
        instance = self.db.session.query(self.model).get_or_404(instance_id)
        return instance
