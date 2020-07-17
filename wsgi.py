from src.lore_log import API
from migrate import Migration
import sqlite3
import os

data_dir = os.environ["LL_API_DATA"]
migration_dir = os.environ["LL_API_MIGRATION_DIR"]

sql_conn = sqlite3.connect(os.path.join(data_dir, "db.sqlite"))
migration = Migration(migration_dir, sql_conn)
migration()

application = API(sql_conn, data_dir)
