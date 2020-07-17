import sqlite3
from src.lore_log import API
from migrate import Migration
import os
from wsgiref import simple_server

db = sqlite3.Connection("temp.sqlite")
Migration(os.path.dirname(os.path.realpath(__file__)) + "/db/sqlite/migrations", db)()

app = API(db, os.path.dirname(os.path.realpath(__file__)))

simple_server.make_server("0.0.0.0", 4242, app).serve_forever()
