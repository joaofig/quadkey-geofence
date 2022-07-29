import contextlib
import sqlite3
import os


class BaseDb(object):

    def __init__(self, folder='./data', file_name='qk-fences.db'):
        self.db_folder = folder
        self.db_file_name = os.path.join(folder, file_name)

    def connect(self):
        return sqlite3.connect(self.db_file_name, check_same_thread=False)

    def execute_sql(self, sql, parameters=[], many=False):
        conn = self.connect()
        cur = conn.cursor()
        if not many:
            cur.execute(sql, parameters)
        else:
            cur.executemany(sql, parameters)
        conn.commit()
        cur.close()
        conn.close()

    def query(self, sql, parameters=[]):
        conn = self.connect()
        cur = conn.cursor()
        result = list(cur.execute(sql, parameters))
        cur.close()
        conn.close()
        return result

    @contextlib.contextmanager
    def query_iterator(self, sql, parameters=[]):
        conn = self.connect()
        cur = conn.cursor()
        yield cur.execute(sql, parameters)
        cur.close()
        conn.close()

    def query_scalar(self, sql, parameters=[]):
        res = self.query(sql, parameters)
        return res[0][0]

    def insert_list(self, sql_cache_key, values):
        conn = self.connect()
        cur = conn.cursor()
        sql = self.sql_cache.get(sql_cache_key)

        cur.executemany(sql, values)

        conn.commit()
        cur.close()
        conn.close()
