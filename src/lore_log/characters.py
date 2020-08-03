from .resource import Resource
from .model import Model
import falcon
from sqlite3 import IntegrityError


class CharacterModel(Model):
    fields = ["id", "name", "race", "level", "class", "class_level", "secondary_class", "secondary_class_level",
              "alignment", "str",  "dex", "con", "int", "wis", "cha", "attr_stats_other", "attributes_public",
              "is_public", "is_pc", "creator_id", "campaign_id", "description", "notes", "sheet_url"]
    alias_fields = {"class_level": "primary_class_level", "class": "primary_class", "str": "attr_str_1",
                    "dex": "attr_dex_2", "con": "attr_con_3", "int": "attr_int_4", "wis": "attr_wis_5",
                    "cha": "attr_cha_6"
                    }
    table_name = "character"
    exception_map = {
        IntegrityError: falcon.HTTPBadRequest("Duplicate Character exists in this campaign")
    }


class Characters(Resource):
    def on_post(self,  req: falcon.Request, res: falcon.Response):
        """ Create a new character. Any authenticated user may create a character """
        character = CharacterModel.from_req(req)
        self.create(character, res)

    def on_get(self, req: falcon.Request, res: falcon.Response):
        """ Retrieve a list of characters, not a single record """
        user_id = req.context["user"]['id']
        campaign_id = req.context["user"]['campaign']
        c = self._db.cursor()
        # TODO paginate
        rows = c.execute("""
        SELECT [id], [name], [race], [level], [primary_class], [primary_class_level], [is_pc], [is_public]
        FROM character
        WHERE (is_public=1 OR creator_id=?) AND campaign_id=?
        """, (user_id, campaign_id)).fetchall()
        characters = []
        for row in rows:
            characters.append({
                'id': row[0],
                'name': row[1],
                'race': row[2],
                'level': row[3],
                'class': row[4],
                'class_level': row[5],
                'is_pc': bool(row[6]),
                'is_public': bool(row[7])
            })
        res.media = characters
        res.status = falcon.HTTP_OK


class Character(Resource):
    def on_get(self, req: falcon.Request, res: falcon.Response, character_id):
        """ Get a single character record, by id """
        c = self._db.cursor()
        row = c.execute("""
        SELECT [id], [name], [race], [level], [description], [primary_class], [primary_class_level], [secondary_class], 
        [secondary_class_level], is_pc, attributes_public, creator_id, alignment, attr_str_1, attr_dex_2, attr_con_3, 
        attr_int_4, attr_wis_5, attr_cha_6, attr_stats_other, is_public, sheet_url, notes
        FROM character
        WHERE id = ? AND (is_public = 1 OR creator_id = ?)
        """, (character_id, req.context['user']['id'])).fetchone()
        if not row:
            raise falcon.HTTPNotFound(title="No character was found with id {} or unauthorized".format(character_id))
        character = {
            'id': row[0],
            'name': row[1],
            'race': row[2],
            'level': row[3],
            'description': row[4],
            'class': row[5],
            'class_level': row[6],
            'secondary_class': row[7],
            'secondary_class_level': row[8],
            'is_pc': bool(row[9]),
            'creator_id': row[11]
        }
        if row[10] or row[11] == req.context['user']['id']:
            character.update({
                'attributes_public': bool(row[10]),
                'alignment': row[12],
                'str': row[13],
                'dex': row[14],
                'con': row[15],
                'int': row[16],
                'wis': row[17],
                'cha': row[18],
                'attr_stats_other': row[19],
            })
        if row[11] == req.context['user']['id']:
            character.update({
                "is_public": bool(row[20]),
                "sheet_url": row[21],
                "notes": row[22]
            })
        res.media = character
        res.status = falcon.HTTP_OK

    def on_patch(self, req: falcon.Request, res: falcon.Response, character_id):
        """ Update a single, existing character record """
        # Get the character to ensure the user is authorized to update
        self.update(CharacterModel, req, character_id)
