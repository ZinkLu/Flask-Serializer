from six import string_types


class CachedModel(object):
    # _model_str, _model, _column_str, _column = None

    def __get__(self, instance, owner):
        if getattr(instance, "_first_set", None):
            # 重写掉_model
            instance._model = None
            instance._model_str = instance._first_set

        if getattr(instance, "_model", None):
            return instance._model

        model_str = instance._model_str

        instance._model = instance.db.Model._decl_class_registry[model_str]
        return instance._model

    def __set__(self, instance, value):
        if isinstance(value, string_types):
            instance._model_str = value
        else:
            instance._model = value


class CachedField(object):

    def __get__(self, instance, owner):
        if getattr(instance, "_column", None) is not None:
            return instance._column

        if instance._column_str is None:
            instance._column_str = instance.field_name

        instance._column = getattr(instance.model, instance._column_str)
        return instance._column

    def __set__(self, instance, value):
        """
        value None
            model = instance.model
            column = getattr(model, instance.field_name)

        value 字符串:
            1. . in value:
                model_str, column_str = value.split('.')
                model = mapperlib.class_mapper(model_str, configure=False)
                column = getattr(model, instance.field_name)

            2. . not in value:
                model = instance.model
                column = getattr(model, value)

        value 非字符串: Mapper.column对象
            1. instance._cache = value
        :param instance:
        :param value:
        :return:
        """
        if value is None:
            instance._column_str = None
            return

        if isinstance(value, string_types):
            if "." in value:
                instance._first_set, instance._column_str = value.split(".")
            else:
                instance._column_str = value
            return

        setattr(instance, "_column", value)
