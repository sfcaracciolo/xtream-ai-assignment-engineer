from flask import g
import sqlite3
from src import DB_FILE

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILE)
    return db

def get_header(cur):
    return [l[0] for l in cur.description]

def get_data(cur, rv):
    h = get_header(cur)
    return [{k:v for k, v in zip(h, row)} for row in rv]