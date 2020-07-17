import sqlite3 as sqlite
from .model import Model
from .utils import generate_new_id
import falcon
from typing import ClassVar
from os import remove, path


class Resource:

    def __init__(self, db: sqlite.Connection, data_path: str):
        self._db = db
        self._path = data_path

    def create(self, model: Model, res: falcon.Response):
        if model.has_external_file_name() and model.rich_description:
            model.external_file_name = generate_new_id()
            with open(path.join(self._path, model.external_file_name), "w") as f:
                f.write(model.rich_description)
        model.insert(self._db)
        self._db.commit()
        res.media = model.to_dict()
        res.status = falcon.HTTP_201

    def update(self, model: ClassVar, req: falcon.Request, res_id):
        has_file = model.has_external_file_name()
        c = self._db.cursor()
        row = c.execute("SELECT {} FROM {} WHERE creator_id=? AND id=?".format(
            "[external_file_name]" if has_file else model.fields[0], model.table_name),
            (req.context['user']['id'], res_id)
        ).fetchone()

        if not row:
            raise falcon.HTTPNotFound("No resource found with id {} or unauthorized".format(res_id))

        obj = model.from_req(req)
        if has_file and obj.rich_description:
            if row[0]:
                obj.external_file_name = row[0]
            else:
                obj.external_file_name = generate_new_id()
            with open(path.join(self._path, obj.external_file_name), "w") as f:
                f.write(obj.rich_description)
        elif has_file and row[0]:
            # The user deleted all rich description content, so lets delete the file
            remove(row[0])
            obj.external_file_name = ""
        obj.update(self._db)
        self._db.commit()
