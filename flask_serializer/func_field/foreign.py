# -*- coding: utf-8 -*-
from . import FieldFunctionBase


class Foreign(FieldFunctionBase):

    def __init__(self, foreign_key_column):
        self.column = foreign_key_column
        self._is_init = False

    def _init_foreign(self):
        """
        初始化
        :return:
        """
        if len(self.column.foreign_keys) != 1:
            raise ValueError("{}不是一个外键列".format(
                self.column.table.name + ":" + self.column.name))

        self.one_table = list(self.column.foreign_keys)[0].column.table
        self.many_table = self.column.table

        if len(self.one_table.primary_key.columns_autoinc_first) != 1:
            raise ValueError("{}找不到主键".format(self.one_table.name))
        self.many_primary_key = self.one_table.primary_key.columns_autoinc_first[0]

        if len(self.many_table.primary_key.columns_autoinc_first) != 1:
            raise ValueError("{}找不到主键".format(self.many_table.name))

        self.one_primary_key = self.many_table.primary_key.columns_autoinc_first[0]

    def foreign_check(self, foreign_ids):
        """
        :param db: Flask-Sqlalchemy instance
        :param foreign_ids: 外键int 或者 list(int)
        检查模型的外键是否存在
        :return: bool
        """
        if not self._is_init:
            self._init_foreign()

        if foreign_ids is None:
            return True

        # get_foreign_key column
        if isinstance(foreign_ids, int):
            if foreign_ids <= 0 or \
                    (not self.db.session.query(self.many_primary_key).filter(
                        self.many_primary_key == foreign_ids).first()):
                return False

        elif isinstance(foreign_ids, list) and foreign_ids:
            relations = self.db.session.query(self.many_primary_key).filter(
                self.many_primary_key.in_(foreign_ids)).all()
            if len(relations) != len(foreign_ids):
                return False

        return True

    def update_foreign(self, one_id, foreign_ids):
        """
        UPDATE many_side SET foreign_key = one_id WHERE many_side.id IN (foreign_ids)
        :param db: Flask-Sqlalchemy instance
        :param one_id: 一端的id
        :param foreign_ids: 外键id, 如果是列表, 则更新多段; 如果是一端, SQLAlchemy会处理的
        :return:
        """
        if isinstance(foreign_ids, list):
            self.db.session.execute(
                self.many_table.update()
                    .values(**{self.column.name: one_id}).
                where(self.many_primary_key.in_(foreign_ids)))
        return
