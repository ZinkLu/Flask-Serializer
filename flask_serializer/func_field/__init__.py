from flask_serializer.cache_object.cached import CachedModel, CachedField


class FieldFunctionBase(object):
    """
    这里类只能在filed中发光发热, 不能单独使用
    """

    db = None

    _model_str = _column_str = field_name = None  # type: str

    model = CachedModel()

    column = CachedField()

    def full_init_self(self, db, field_name, model):
        """cls hold db while self hold field_name, and model"""
        if not self.db:
            self.__class__.db = db

        self.field_name = field_name
        self.model = model  # property
