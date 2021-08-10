import sqlite3
from settings import *


def chk_db(conn_str):
    db = sqlite3.connect(conn_str)
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    if not cursor.fetchall():
        cursor.execute("""CREATE TABLE IF NOT EXISTS routers (
                        id	INTEGER NOT NULL,
                        name	text NOT NULL DEFAULT 'SW',
                        mac	text NOT NULL DEFAULT '',
                        ip	text NOT NULL DEFAULT '',
                        exclports	text NOT NULL DEFAULT '',
                        stackmaster	INTEGER NOT NULL DEFAULT 0,
                        stacknum	intager NOT NULL DEFAULT 0,
                        t	text NOT NULL DEFAULT '',
                        box	INTEGER NOT NULL DEFAULT 1,
                        fa	INTEGER NOT NULL DEFAULT 24,
                        gi	INTEGER NOT NULL DEFAULT 2,
                        descr	TEXT NOT NULL DEFAULT '',
                        numinbox	INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(id AUTOINCREMENT)
                        );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS ports (
                        id_r	intager,
                        port	text NOT NULL DEFAULT '',
                        mac	text NOT NULL DEFAULT '',
                        ip	text NOT NULL DEFAULT '',
                        name	text NOT NULL DEFAULT '',
                        t	text DEFAULT '',
                        onoff	intager NOT NULL DEFAULT 2,
                        descr	TEXT NOT NULL DEFAULT '',
                        speed	INTEGER NOT NULL DEFAULT 0
                        );""")
        db.commit()
    cursor.close()
    db = None


def db_connector(func):
    """decorator"""
    def with_connection_(*args, **kwargs):
        db = sqlite3.connect(os.path.join(DB_DIR, s_values['dbfile']))
        try:
            rv = func(db, *args, **kwargs)
        except Exception:
            db.rollback()
            raise
        else:
            db.commit()
        finally:
            db.close()
        return rv
    return with_connection_
