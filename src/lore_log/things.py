from .resource import Resource
from .model import Model
import falcon
import os


class ThingModel(Model):
    fields = ["id", "name", "type", "weight", "price", "price_unit", "description", "external_file_name", "is_public",
              "owner_id", "campaign_id", "creator_id"]
    summary_fields = {"id", "name", "type", "weight", "price", "price_unit", "description"}
    extra_fields = {"rich_description"}
    autoincrement_id = True
    table_name = "thing"


class Things(Resource):
    def on_post(self, req: falcon.Request, res: falcon.Response):
        thing = ThingModel.from_req(req)
        self.create(thing, res)

    def on_get(self, req: falcon.Request, res: falcon.Response):
        c = self._db.cursor()
        rows = c.execute("""SELECT {} FROM [thing] WHERE campaign_id = ? AND (creator_id=? OR is_public=1)""".format(
            ", ".join(f"[{field}]" for field in ThingModel.fields)),
            (req.context['user']['campaign'], req.context['user']['id'])).fetchall()
        things = []
        for row in rows:
            things.append(ThingModel.from_db(row).to_summary_dict())
        res.media = things


class Thing(Resource):
    def on_get(self, req: falcon.Request, res: falcon.Response, thing_id):
        c = self._db.cursor()
        row = c.execute("""
        SELECT {} FROM [thing] WHERE id = ? AND (is_public=1 OR creator_id=?)
        """.format(",".join(f"[{field}]" for field in ThingModel.fields)),
                        (thing_id, req.context['user']['id'])).fetchone()
        if not row:
            raise falcon.HTTPNotFound("No thing found with id {} or unauthorized".format(thing_id))
        thing = ThingModel.from_db(row)
        if thing.external_file_name:
            with open(os.path.join(self._path, thing.external_file_name)) as f:
                thing.rich_description = f.read()
        res.media = thing.to_dict()

    def on_patch(self, req: falcon.Request, res: falcon.Response, thing_id):
        self.update(ThingModel, req, thing_id)
