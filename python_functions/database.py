import psycopg2
from psycopg2.extras import register_json
class Database:
    def __init__(self, host, database, user, password, port):
        self.password = password
        self.host = host
        self.db_name = database
        self.user = user
        self.port = port
        register_json(oid=3802, array_oid=3807)

    def getConnection(self):
        conn = psycopg2.connect(host=self.host, dbname=self.db_name, user=self.user, password=self.password, port=self.port)
        return conn


    def select(self, query, parameter=[]):
        conn = None
        try:
            conn = self.getConnection()
            cursor = conn.cursor()
            cursor.execute(query, parameter)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except psycopg2.DatabaseError as error:
            raise error
        finally:
            if conn is not None:
                conn.close()

    def insert(self, query):
        conn = None
        try:
            conn = self.getConnection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
        except psycopg2.DatabaseError as error:
            raise error
        finally:
            if conn is not None:
                conn.close()
