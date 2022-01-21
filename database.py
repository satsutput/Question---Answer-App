from sqlite3.dbapi2 import connect
from flask import g
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor

'''def connect_db():
    sql = sqlite3.connect('questions.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite3_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db'''

def connect_db():
    conn = psycopg2.connect('postgres://wuuchmsoswwubv:bbe36f26d1ea8d58eebeefcb87f25b67b19dcf6bbad1ef1f8cebc72aafbb5fad@ec2-3-225-41-234.compute-1.amazonaws.com:5432/d5b34itnocv6qt', cursor_factory=DictCursor)
    conn.autocommit = True
    return conn

def get_db():
    db = connect_db()

    if 'postgres_db_conn' not in g:
        g.postgres_db_conn = db

    return g.postgres_db_conn

def init_db():
    db = connect_db()
    cur = db.cursor()

    cur.execute(open('schema.sql', 'r').read())
    db.close()

def init_admin():
    db = connect_db()
    cur = db.cursor()
    cur.execute('update users set admin = True where name = %s', ('admin', ))