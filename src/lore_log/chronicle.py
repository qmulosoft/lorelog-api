from .resource import Resource
from .model import Model
import falcon
from .utils import generate_new_id
import os


class ChronicleEntryModel(Model):
    fields = ['id', 'title', 'tick', 'relation_type', 'external_file_name', 'campaign_id', 'creator_id', 'is_public']
    extra_fields = {"rich_description", "relation_id"}
    summary_fields = {"id", "title", "tick", "is_public", "relation_type"}
    autoincrement_id = False
    table_name = "chronicle_entry"


valid_types = {"character", "faction", "domain", "place", "thing"}


class ChronicleEntries(Resource):

    def on_get(self, req: falcon.Request, res: falcon.Response):
        where = "WHERE campaign_id = ? AND (creator_id = ? OR is_public=1)"
        where_args = [req.context['user']['campaign'], req.context['user']['id']]
        join = ""
        if req.params.get("relation_type", None) is not None:
            type = req.params["relation_type"]
            join = f"JOIN {type}_chronicle subset ON subset.chronicle_entry_id = chronicle.id"
            if req.params.get("relation_id"):
                where += f" AND subset.{type}_id = ?"
                where_args.append(req.params.get('relation_id'))
        sql = "SELECT {} FROM chronicle_entry chronicle {} {} ORDER BY tick DESC".format(
            ",".join(f"chronicle.{field}" for field in ChronicleEntryModel.fields),
            join,
            where
        )
        cursor = self._db.cursor()
        rows = cursor.execute(sql, where_args)
        entries = []
        for row in rows:
            entry = ChronicleEntryModel.from_db(row).to_summary_dict()
            entries.append(entry)
        res.media = entries

    def on_post(self, req: falcon.Request, res: falcon.Response):
        entry = ChronicleEntryModel.from_req(req)
        if entry.relation_type not in valid_types:
            raise falcon.HTTPBadRequest(title="invalid relation type: {}".format(entry.relation_type))
        if not entry.relation_id:
            raise falcon.HTTPBadRequest(title="missing required relation_id field")
        if not entry.rich_description:
            raise falcon.HTTPBadRequest(title="chronicle entries require a description")
        cursor = self._db.cursor()
        row = cursor.execute("""SELECT [id] FROM [{}] WHERE id=? AND creator_id=? AND campaign_id=?""".format(
            entry.relation_type), (entry.relation_id, req.context['user']['id'], req.context['user']['campaign'])
        ).fetchone()
        if not row:
            raise falcon.HTTPNotFound(title="no such {} exists or unauthorized".format(entry.relation_type))
        entry.id = generate_new_id()
        if not entry.tick:
            # Get the next tick in the sequence if they didn't populate tick explicitly
            row = cursor.execute("SELECT [tick] FROM chronicle_entry WHERE campaign_id = ? ORDER BY [tick] DESC LIMIT 1",
                                 (req.context['user']['campaign'],)).fetchone()
            if not row:
                row = cursor.execute("SELECT [start_tick] FROM campaign WHERE id = ?",
                                     (req.context['user']['campaign'],)).fetchone()
                entry.tick = int(row[0])
            else:
                entry.tick = int(row[0]) + 1000
        self.create(entry, res)
        sql = f"""INSERT INTO {entry.relation_type}_chronicle 
            ([{entry.relation_type}_id], [chronicle_entry_id])
            VALUES (?, ?)
        """
        cursor.execute(sql, (entry.relation_id, entry.id))
        self._db.commit()


class ChronicleEntry(Resource):
    def on_get(self, req: falcon.Request, res: falcon.Response, entry_id):
        c = self._db.cursor()
        row = c.execute("""
                 SELECT {}
                 FROM chronicle_entry
                 WHERE id=? AND (creator_id=? OR is_public=1)
                 """.format(",".join(f"[{field}]" for field in ChronicleEntryModel.fields)),
                        (entry_id, req.context['user']['id'])).fetchone()
        if not row:
            raise falcon.HTTPNotFound(title="No entry found with id {} or unauthorized".format(entry_id))
        entry = ChronicleEntryModel.from_db(row)
        related_row = c.execute(f"""
        SELECT [{entry.relation_type}_id] FROM {entry.relation_type}_chronicle WHERE chronicle_entry_id=?
        """, (entry.id,)).fetchone()
        entry.relation_id = related_row[0]
        if entry.external_file_name:
            with open(os.path.join(self._path, entry.external_file_name)) as f:
                entry.rich_description = f.read()
        res.media = entry.to_dict()

    def on_patch(self, req: falcon.Request, res: falcon.Response, entry_id):
        self.update(ChronicleEntryModel, req, entry_id)
