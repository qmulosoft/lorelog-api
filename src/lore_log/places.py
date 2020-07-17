from .resource import Resource
import falcon
from .model import Model
import os


class PlaceModel(Model):
    fields = ["id", "name", "type", "map_url", "description", "external_file_name", "is_public", "campaign_id", "creator_id"]
    extra_fields = {"rich_description"}
    summary_fields = {"id", "name", "type", "description", "is_public"}
    table_name = "place"
    autoincrement_id = True


valid_types = {"domain", "region", "city", "dungeon"}


class Places(Resource):

    def on_post(self, req: falcon.Request, res: falcon.Response):
        place = PlaceModel.from_req(req)
        if place.type not in valid_types:
            raise falcon.HTTPBadRequest("Invalid place type. Must be domain, region, city or dungeon")
        if place.type == "domain":
            raise falcon.HTTPBadRequest("Cannot create multiple domains in a campaign")
        self.create(place, res)

    def on_get(self, req: falcon.Request, res: falcon.Response):
        where = "WHERE [campaign_id] = ? AND (is_public=1 OR creator_id=?)"
        where_args = [req.context['user']['campaign'], req.context['user']['id']]
        if req.params.get("type", None) is not None:
            where += " AND [type] = ?"
            where_args.append(req.params.get("type"))
        c = self._db.cursor()
        rows = c.execute("""SELECT {} FROM [place] {}""".format(
            ", ".join(f"[{field}]" for field in PlaceModel.fields), where), where_args).fetchall()
        places = []
        for row in rows:
            places.append(PlaceModel.from_db(row).to_summary_dict())
        res.media = places


class Place(Resource):

    def on_get(self, req: falcon.Request, res: falcon.Response, place_id):
        """ GET a single place """
        c = self._db.cursor()
        row = c.execute("""
         SELECT {}
         FROM place
         WHERE id=? AND (creator_id=? OR is_public=1)
         """.format(",".join(f"[{field}]" for field in PlaceModel.fields)), (place_id, req.context['user']['id'])).fetchone()
        if not row:
            raise falcon.HTTPNotFound("No place found with id {} or unauthorized".format(place_id))
        place = PlaceModel.from_db(row)
        if place.external_file_name:
            with open(os.path.join(self._path, place.external_file_name)) as f:
                place.rich_description = f.read()
        res.media = place.to_dict()

    def on_patch(self, req: falcon.Request, res: falcon.Response, place_id):
        self.update(PlaceModel, req, place_id)
