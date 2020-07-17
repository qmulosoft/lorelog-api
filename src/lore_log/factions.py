from .model import Model
from .resource import Resource
import os
import falcon


class FactionModel(Model):
    fields = ["id", "name", "description", "external_file_name", "is_public", "campaign_id", "creator_id"]
    table_name = "faction"
    extra_fields = {"rich_description"}
    autoincrement_id = True


class Factions(Resource):
    """ Implements actions to act on the collection of factions """

    def on_get(self, req: falcon.Request, res: falcon.Response):
        """ Retrieve a list of all factions """
        c = self._db.cursor()
        rows = c.execute("""
        SELECT [id], [name], [description], [is_public] FROM faction
        WHERE campaign_id = ? AND (is_public = 1 OR creator_id = ?)
        """, (req.context["user"]["campaign"], req.context["user"]["id"]))
        factions = []
        for row in rows:
            factions.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "is_public": row[3]
            })
        res.media = factions

    def on_post(self, req: falcon.Request, res: falcon.Response):
        """ Create a new faction in the current campaign """
        faction = FactionModel.from_req(req)
        self.create(faction, res)


class Faction(Resource):

    def on_get(self, req: falcon.Request, res: falcon.Response, faction_id: str):
        """ GET a single faction """
        c = self._db.cursor()
        row = c.execute("""
        SELECT [id], [name], [description], external_file_name, is_public, campaign_id, creator_id FROM faction
        WHERE id=? AND (creator_id=? OR is_public=1)
        """, (faction_id, req.context['user']['id'])).fetchone()
        if not row:
            raise falcon.HTTPNotFound("No faction found with id {} or unauthorized".format(faction_id))
        faction = FactionModel.from_db(row)
        if faction.external_file_name:
            with open(os.path.join(self._path, faction.external_file_name)) as f:
                faction.rich_description = f.read()
        res.media = faction.to_dict()

    def on_patch(self, req: falcon.Request, res: falcon.Response, faction_id: str):
        """ Update a single faction object """
        self.update(FactionModel, req, faction_id)
