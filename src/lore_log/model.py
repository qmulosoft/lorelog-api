import sqlite3
from abc import ABC
import falcon


class Model(ABC):

    fields = []
    # Used for storing values that have a different db column name than is used in json representation
    # format: {name: db_name}
    alias_fields = {}
    # Used for fields that will come from the API but will not be written to the database. Typically due to additional
    # processing being necessary.
    extra_fields = set()
    # Used to get a subset of fields for returning results in List views (GET without an id)
    summary_fields = set()
    autoincrement_id = True
    table_name = ""
    exception_map = {}

    def __init__(self, **kwargs):
        for key in self.alias_fields.keys():
            if key not in self.fields and key not in self.extra_fields:
                raise ValueError("Invalid alias_field value: {} does not exist in class fields".format(key))

        self._kvs = {}
        for each in self.fields + list(self.extra_fields):
            self._kvs[each] = None
        for k, v in kwargs.items():
            if k in self.fields or k in self.extra_fields:
                self._kvs[k] = v
            else:
                raise NameError("Invalid field name {}".format(k))

    def __getattr__(self, item):
        return self._kvs[item]

    def __setattr__(self, key, value):
        if key in self.fields or key in self.extra_fields:
            self._kvs[key] = value
        else:
            super().__setattr__(key, value)

    @classmethod
    def has_external_file_name(cls):
        return "external_file_name" in cls.fields

    @classmethod
    def from_db(cls, row):
        kvs = {}
        for i, each in enumerate(row):
            kvs[cls.fields[i]] = each
        return cls(**kvs)

    @classmethod
    def from_media(cls, data: dict):
        return cls(**data)

    @classmethod
    def from_req(cls, req: falcon.Request):
        c = cls(**req.media)
        if "campaign_id" in c.fields:
            c.campaign_id = req.context["user"]["campaign"]
        if "creator_id" in c.fields:
            c.creator_id = req.context["user"]["id"]
        return c

    def to_dict(self) -> dict:
        return self._kvs

    def to_summary_dict(self) -> dict:
        d = {}
        for k, v in self._kvs.items():
            if k in self.summary_fields:
                d[k] = v
        return d

    def execute_sql(self, c: sqlite3.Cursor, sql: str, args):
        try:
            c.execute(sql, args)
        except Exception as e:
            if type(e) in self.exception_map:
                raise self.exception_map[type(e)]
            else:
                raise e

    def select_fields(self, index=0):
        columns = []
        for each in self.fields[index:]:
            if self._kvs[each] is None:
                continue
            if each in self.alias_fields:
                each = self.alias_fields[each]
            columns.append("[" + each + "]")
        return columns

    def insert(self, db: sqlite3.Connection):
        c = db.cursor()
        columns = self.select_fields(1 if self.autoincrement_id else 0)
        values = ",".join(["?"] * len(columns))
        columns = ",".join(columns)
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})"
        self.execute_sql(c, sql, [self._kvs[each] for each in self.fields if self._kvs[each] is not None])
        if self.autoincrement_id:
            self._kvs[self.fields[0]] = c.lastrowid

    def update(self, db: sqlite3.Connection):
        c = db.cursor()
        columns = [f"{field}=?" for field in self.select_fields(1)]
        columns = ",".join(columns)
        sql = f"UPDATE [{self.table_name}] SET {columns} WHERE [{self.fields[0]}]=?"
        self.execute_sql(c, sql, [self._kvs[each] for each in self.fields[1:] if self._kvs[each] is not None] + [self._kvs[self.fields[0]]])
