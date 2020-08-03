import falcon
from .resource import Resource
from .model import Relation, Model
from .characters import CharacterModel
from .factions import FactionModel


class CharacterFactionModel(Model):
    fields = ["character_id", "faction_id", "is_public", "role", "reputation", "creator_id"]
    extra_fields = {"relation_id"}
    table_name = "character_faction"


class CharacterFactionRelation(Relation):
    model = CharacterFactionModel
    this = CharacterModel
    that = FactionModel


class CharacterRelations(Resource):

    def validate_req(self, req: falcon.Request, character_id, relation_type):
        if relation_type not in ("factions",):
            raise falcon.HTTPBadRequest(title=f"invalid relation type for character: {relation_type}")
        c = self._db.cursor()
        row = c.execute(f"""
            SELECT [id] FROM [character] WHERE id = ? AND (is_public = 1 OR creator_id = ?)
        """, (character_id, req.context['user']['id'])).fetchone()
        if row is None:
            raise falcon.HTTPNotFound(f"no such character with id {character_id} exists or unauthorized")
        # TODO validate the relation being added exists. Need to figure out permissions, here

    def on_post(self, req: falcon.Request, res: falcon.Response, character_id, relation_type):
        self.validate_req(req, character_id, relation_type)
        # the front end generalizes all this to reuse components
        req.media['character_id'] = character_id
        req.media['faction_id'] = req.media['relation_id']
        del req.media['relation_id']
        relation = CharacterFactionRelation()
        relation.from_req(req)
        relation.add(self._db)
        res.status = falcon.HTTP_CREATED
        self._db.commit()

    def on_get(self, req: falcon.Request, res: falcon.Response, character_id, relation_type):
        self.validate_req(req, character_id, relation_type)
        relation = CharacterFactionRelation()
        rows = relation.find_all(self._db, req, character_id)
        relations = []
        c = self._db.cursor()
        for row in rows:
            model = CharacterFactionRelation.model.from_db(row)
            # hydrate the faction name for summary view in the UI
            row = c.execute(f"SELECT [name] FROM {relation.that.table_name} WHERE id=?", (model.faction_id,)).fetchone()
            result = {"primary_id": character_id, "relation_id": model.faction_id, "relation_name": row[0],
                      "role": model.role, "reputation": model.reputation, "is_public": model.is_public,
                      "creator_id": model.creator_id}
            relations.append(result)
        res.media = relations


class CharacterRelation(Resource):

    def on_delete(self, req: falcon.Request, res: falcon.Response, character_id, relation_type, relation_id):
        if relation_type not in ("factions",):
            raise falcon.HTTPBadRequest(f"invalid relation type for character: {relation_type}")
        c = self._db.cursor()
        # TODO permissions. Should probably be set in campaign permissions whether users can add relationships to
        # characters they own even if they don't own the faction, etc.
        row = c.execute(f"""SELECT [faction_id] FROM [character_faction] WHERE faction_id = ? and character_id = ?
         AND creator_id = ?""", (relation_id, character_id, req.context['user']['id'])).fetchone()
        if row is None:
            raise falcon.HTTPNotFound(title="no such character faction relation exists or unauthorized")
        c.execute(f"DELETE FROM [character_faction] WHERE character_id = ? and faction_id = ?",
                  (character_id, relation_id))
        self._db.commit()
        res.status = falcon.HTTP_NO_CONTENT
